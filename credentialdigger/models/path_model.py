import re

from .base_model import BaseModel


class PathModel(BaseModel):

    def __init__(self):
        self.fp_keywords = re.compile(
            r'(con)?test|example|sample|demo^(cra)?^(graph)?|package-lock|'
            'makefile|gruntfile|node_modules|site-packages|\.md$|css$|\.rst$')

    def analyze(self, discovery):
        """ Analyze a path and predict whether it is a false positive or not.

        Parameters
        ----------
        discovery: dict
            A discovery

        Returns
        -------
        bool
            True if the discovery is classified as false positive (i.e., spam)
        """
        return bool(self.fp_keywords.search(discovery['file_name'].lower()))

    def analyze_batch(self, discoveries):
        """ Classify discoveries according to their paths.
        Change each discovery state in-place.

        Parameters
        ----------
        discoveries: list of dict
            The discoveries to classify

        Returns
        -------
        discoveries: list of dict
            The discoveries, with states updated according to their paths
        """
        path_dict = {}

        for discovery in discoveries:
            # Ignore already classified discoveries
            if discovery['state'] != 'new':
                continue
            # Transform all the paths in lowercase
            preprocessed_path = discovery['file_name'].lower()

            if preprocessed_path in path_dict:
                # This path has already been classified, so don't re-classify
                # it
                discovery['state'] = path_dict[preprocessed_path]
                continue

            # Run the classification task
            if self.fp_keywords.search(preprocessed_path):
                path_dict[preprocessed_path] = 'false_positive'
                discovery['state'] = 'false_positive'
            else:
                path_dict[preprocessed_path] = 'new'

        return discoveries
