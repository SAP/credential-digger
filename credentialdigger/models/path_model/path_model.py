import re

from nltk.stem import PorterStemmer

from ..base_model import BaseModel


class PathModel(BaseModel):

    def __init__(self, model='path_model', binary='path_model.bin'):
        """ This class classifies a discovery as a false positive according to
        its file path.

        Parameters
        ----------
        model: str, default `path_model`
            The name of the ML model
        binary: str, default `model_path.bin`
            The name of the binary
        """
        super().__init__(super().find_model_file(model, binary))

    def analyze(self, discovery):
        """ Analyze a path and predict whether it is a false positive or not.

        Parameters
        ----------
        discovery: dict
            A discovery

        Returns
        -------
        bool
            True if the discovery is classified as false positive
        """
        # Transform the path of this discovery into a string of words
        vector = self._preprocess_path(discovery['file_name'].strip())

        # Launch the prediction of the vector
        label = self.model.predict(vector)[0][0]

        # Get the prediction value related to the current path (the vector)
        # If prediction == __label__1, then it is detected as false positive
        # If not detected it does not mean that it is not a false positive:
        # it may still be a false positive, but it is not possible to detect it
        # with this model
        return label == '__label__1'

    def _get_ext(self, path):
        """ Extract the extension from the path.

        In case there is an extension `.erb`, remove it and search for another
        extension.

        Params
        ------
        path: str
            The file path

        Returns
        -------
        str
            The extension of the path, if any, `no_ext` otherwise

        Examples
        --------
        >>> print(self._get_ext('mypath.py'))
        'py'

        >>> print(self._get_ext('some/path/without/extension'))
        'no_ext'

        >>> print(self._get_ext('some/path/file.java.erb'))
        'java'

        >>> print(self._get_ext('some/path/file.erb'))
        'no_ext'
        """
        # Get extension (split the last .)
        vec = path.rsplit('.', 1)
        if len(vec) == 2:
            vec[1] = vec[1].lower()
            if vec[1] == 'erb':
                # Remove erb extension and get the nested one
                vec1 = vec[0].rsplit('.', 1)
                if len(vec1) == 2:
                    return vec1[1].lower()
                else:
                    return 'no_ext'
            else:
                return vec[1]
        else:
            # The split did not have an extension
            return 'no_ext'

    def _stem(self, ext, words):
        """ Find the root of each word contained in the path, excluding the
        extension.

        Params
        ------
        ext: str
            The extension of the file
        words: list
            A list of words

        Returns
        -------
        list
            A list containing root words and the extension (if any)
        """
        stemmer = PorterStemmer()
        if ext != 'no_ext':
            return list(map(stemmer.stem, words[:-1])) + [ext]
        else:
            return list(map(stemmer.stem, words))

    def _preprocess_path(self, path):
        """ Convert all the words contained in a path into their root.

        Parameters
        ----------
        path: string
            The file path

        Returns
        -------
        str
            A string of root words
        """
        # Replace non alphanumeric characters
        processed_path = re.sub('[^A-Za-z ]', ' ', path)
        # Remove numbers
        processed_path = ''.join(filter(lambda c: not c.isdigit(),
                                        processed_path))
        # Split the path in correspondence with spaces
        tokens = processed_path.split()
        # Split CamelCase tokens
        tokens = map(lambda word: re.sub('([A-Z][a-z]+)',
                                         r' \1', re.sub('([A-Z]+)', r'\1',
                                                        word)),
                     tokens)
        # Translate tokens to lowercase
        tokens = map(lambda s: s.lower(), tokens)
        # Find the root of each token
        stems = self._stem(self._get_ext(path), list(tokens))
        return ' '.join(stems)
