import re
from difflib import SequenceMatcher

import fasttext
from string_utils import snake_case_to_camel

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
        raw_data = discovery['snippet']
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

        # Classify as a 'Leak' if this is a private key.
        if self._check_private_key(data):
            return False

        # We ignore snippets that look like regular phrases with
        # no assignment
        if self._not_an_assignment(raw_data):
            return True

        # Extract the discovered secret
        # For snippet = 'string password = "123"', we will obtain indices [1,2]
        # index 1: password | index 2: 123
        index_of_value = self._label_preprocess(data)

        # We retrieve only the leaked value to be tested by the classifier
        extracted_value = data[index_of_value[1]]

        if len(extracted_value) <= 3:
            # We ignore any password shorter than or equal to 3
            return True
        else:
            # Predict if the string is a false positive
            label = self.model.predict(extracted_value)[
                0]  # 0=label, 1=probability

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

        Finally, convert words (not strings) from snake_case (i.e., words
        separated by underscores, like in Python convention) to CamelCase
        (i.e., Java convention).

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
        ['password','"#####"', '!@AAA12']
        """
        # Extract all the words in a snippet
        words = re.findall(r'(?<=\').*?(?=\')|(?<=").*?(?=")|[\w\d]+',
                           raw_data)
        # Extract only the words that are between " or ', we refer to them
        # as strings
        strings = re.findall(r'(?<=\').*?(?=\')|(?<=").*?(?=")', raw_data)

        camel_case_words = []
        for w in words:
            # If a word is a string, we do not make any changes to it
            if w in strings:
                camel_case_words.append(w)
            else:
                camel_case_words.append(snake_case_to_camel(w))

        return camel_case_words

    def _label_preprocess(self, words_list):
        """ Output the extracted word from the label of the model.

        Parameters
        ----------
        words_list: list
            A list of words and/or strings

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
        # if we get label=24 but we have only 3 words ==> We assume it means
        # the last word needs to be extracted
        for label in [first_label, second_label]:
            if label > size:
                finish_labels.append(size)
            else:
                finish_labels.append(label)

        return finish_labels

    def _remove_initial_junk(self, snippet):
        """ Remove junk from the beginning of a snippet.

        Parameters
        ----------
        snippet: str
            The code snippet

        Returns
        -------
        str
            The same snippet, "cleaned" on the left
        """
        return re.sub(
            r'^((\s*|\ *)\@\@.*\@\@(\s*|\ *)|(\s*|\ *)\+(\s*|\ *)|(\s*|\ *)\-(\s*|\ *)|(\s*|\ *))',
            '',
            snippet).strip()

    def _not_an_assignment(self, snippet):
        """ Evaluate whether a line of code is an assignment or not.

        The goal is to ignore snippets that look like regular phrases with no
        assignment hints.

        Parameters
        ----------
        snippet: str
            A code snippet (as it appears in its commit diff)

        Returns
        -------
        bool
            True if the snippet contains any symbols that may lead to password
            assignment, False otherwise
        """
        # The following symbols cannot be used to assign a value to a variable
        # Symbols that do so are =, :, <-, ->, <<, >>, etc.
        no_assignment_symbols = ' _.,?!/#|+-\\"\''

        if not any(not c.isalnum() and c not in no_assignment_symbols
                   for c in snippet):
            return True

        return False

    def _check_private_key(self, snippet):
        """ Check if this snippet is the header of a private key.

        Parameters
        ----------
        snippet: str
            A code snippet (as it appears in its commit diff)

        Returns
        -------
        bool
            True if the input is the header of a private key, False otherwise
        """
        base_private_key = ['BEGIN', 'PRIVATE', 'KEY']
        # Return True if similarity ratio >= 85%
        return SequenceMatcher(None, base_private_key, snippet).ratio() >= 0.85
