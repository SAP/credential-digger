import re

import fasttext
import string_utils

from ..base_model import BaseModel

EXTENSIONS = set(['py', 'rb', 'c', 'cpp', 'cs', 'js', 'php', 'h', 'java', 'pl',
                  'go'])
KEYWORDS = set(['def', 'function', 'return', 'class', 'import'])


class SnippetModel(BaseModel):

    def __init__(self,
                 model='snippet_model',
                 binary_classifier='model_classifier.bin',
                 model_extractor='snippet_model',
                 binary_extractor='model_extractor.bin'):
        """ This class classifies a discovery as a false positive according to
        its code snippet.

        First, the extractor model extracts a keypair from the code snippet,
        and then the classifier model classifies the keypair as a false
        positive (or not).

        Parameters
        ----------
        model: str, default `snippet_model`
            The name of the ML model with the classifier
        binary_classifier: str, default `model_classifier.bin`
            The name of the binary for the classifier
        model_extractor: str, default `snippet_model`
            The name of the ML model with the extractor
        binary_extractor: str, default `model_extractor.bin`
            The name of the binary for the extractor
        """
        super().__init__(super().find_model_file(model, binary_classifier))
        self.model_extractor = fasttext.load_model(
            super().find_model_file(model_extractor, binary_extractor))

    def analyze(self, discovery):
        """ Analyze a snippet and predict whether it is a false positive or not.

        Parameters
        ----------
        discovery: dict
            A discovery

        Returns
        -------
        bool
            True if the discovery is classified as false positive
        """
        raw_data = self._remove_initial_junk(discovery['snippet'])

        # In some programming languages, we expect to find a password as a
        # string (thus, surrounded by quotes). If no quote appears in the
        # snippet, then there isn't any hardcoded password
        extension = discovery['file_name'].split('.')[-1]
        if extension in EXTENSIONS:
            s = re.sub('\'\'| \"\"', '', raw_data)
            if '"' not in s and "'" not in s:
                return True

        # Analyze the first word in the snippet
        if raw_data.split()[0] in KEYWORDS:
            # If the first word is a keyword, then return True
            return True

        # Convert data format
        data = self._pre_process(raw_data)

        if len(data) < 2:
            # No need to run the model: we assume this is a false positive
            # since either the snippet is empty or there is just one word
            return True

        if len(data) == 2:
            # No need to pre-process data since we have only two words
            # Predict if the string `word1 + ' ' + word2` is a false positive
            label = self.model.predict(
                data[0] + ' ' + data[1])[0]  # 0=label, 1=probability
        else:
            finish_labels = self._label_preprocess(data)
            # Predict if the string `word1 + ' ' + word2` is a false positive
            label = self.model.predict(
                data[finish_labels[0]] + ' ' +
                data[finish_labels[1]])[0]  # 0=label, 1=probability

        label = label[0]  # label was a tuple of 1 element

        # Last index of the prediction indicates the state
        # 1 = false positive (test, dummy, etc.)
        # 0 = true positive (supposedly)
        return label.split('__')[-1] == '1'

    def _pre_process(self, raw_data):
        """ Extract words from snippet and fit them to the Java convention.

        Find words and strings in `raw_data` and extract them.
        We define as strings any sequence of characters included in `"` or `'`
        and as words any sequence of alphanumeric characters.

        In particular, if a string does not contain characters, it is not
        matched. This is done in order to exclude patterns such as "###" or
        "***". In case the string has a mixed content, it is matched starting
        from the first letter/number (e.g., "!@#QWE123" matches "QWE123").

        Finally, convert words from snake_case (i.e., words separated by
        underscores, like in Python convention) to CamelCase (i.e., Java
        convention).

        Parameters
        ----------
        raw_data: str
            A snippet (as appears in its commit diff)

        Returns
        -------
        list
            A list of strings

        Examples
        --------
        >>> raw_data = 'this is my foo(secret_token_auth, )'
        >>> print(self._pre_process(raw_data))
        ['this', 'is', 'my', 'foo', 'SecretTokenAuth']

        >>> raw_data = 'self.do_something(password="3733tPwd!")'
        >>> print(self._pre_process(raw_data))
        ['self', 'DoSomething', 'password', '3733tPwd!']

        >>> raw_data = '"password": "#####", "!@AAA12")'
        >>> print(self._pre_process(raw_data))
        ['password', 'AAA12']
        """
        # r"((?<=').*?(?=')|(?<=\").*?(?=\")|[a-zA-Z0-9\._@-]+)"
        # Match words and strings
        # In strings, match the content starting from the first character
        # e.g., "****" -> None
        #       "$AAA123!!" -> AAA123!!
        pattern = re.compile(
            r"((?<=')\w\d.*?(?=')|(?<=\")\w\d.*?(?=\")|[\w\d]+)")
        words = re.findall(pattern, raw_data)
        return list(map(string_utils.snake_case_to_camel, words))

    def _label_preprocess(self, words_list):
        """ Output the extracted word from the label of the model.

        Parameters
        ----------
        words_list: list
        model_extractor:

        Returns
        -------
        list
            A list of positions of words

        """
        # Build a data string (needed by the model)
        data = ' '.join(words_list)

        # Count the words in data and get the k most frequent
        extraction = self.model_extractor.predict(data, k=2)
        # Extraction is a list of two tuples:
        # The first tuple are the k most common words
        # The second tuple are the frequecies of those words
        # Example:
        # extraction = [('position1', 'position2', ..., 'positionK'),
        #               ('freq1', 'freq2', ..., 'freqK')]

        first_label, second_label = extraction[0]  # Get words positions
        # probabilities = extraction[1]  # Probabilities to be right

        # Get the numbers (the first occurrence of a word in `data`)
        # Each position has the following format
        # position = '__label__number'
        first_label = int(first_label.split('__')[-1])
        second_label = int(second_label.split('__')[-1])
        size = len(words_list) - 1
        finish_labels = []

        # We need to check if the label number is below the number of words
        # Example:
        # if we get label=24 but only 3 words ==> We assume it means
        # the last word needs to be extracted
        for label in [first_label, second_label]:
            if label > size:
                finish_labels.append(size)
            else:
                finish_labels.append(label)

        return finish_labels

    def _remove_initial_junk(self, snippet):
        """ Remove junk from the beginning of a snippet.
        """
        return re.sub(
            r"^((\s*|\ *)\@\@.*\@\@(\s*|\ *)|(\s*|\ *)\+(\s*|\ *)|(\s*|\ *)\-(\s*|\ *)|(\s*|\ *))",
            "",
            snippet).strip()
