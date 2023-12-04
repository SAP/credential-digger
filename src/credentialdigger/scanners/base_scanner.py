from abc import ABC, abstractmethod


class BaseScanner(ABC):

    def __init__(self, rules):
        self.rules = rules

    @abstractmethod
    def scan(self, repo_url, **kwargs):
        pass


class ResultHandler:

    def __init__(self):
        self.result = None

    def handle_results(self, eid, start, end, flags, context):
        """ Give a structure to the discovery and store it in a variable.

        This method is needed in order to process the result of a scan (it is
        used as a callback function).

        Parameters
        ----------
        eid: int
            The id of the regex that produced the discovery
        start: int
            The start index of the match
        end: int
            The end index of the match
        flags
            Not implemented by the library
        context: list
            Metadata (composed by snippet, filename, hash, line_number)
        """
        snippet, filename, commit_hash, line_number = context

        meta_data = {'file_name': filename,
                     'commit_id': commit_hash,
                     'line_number': line_number,
                     'snippet': snippet,
                     'rule_id': eid,
                     'state': 'new'}

        self.result = meta_data
