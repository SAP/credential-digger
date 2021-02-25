from abc import ABC, abstractmethod


class BaseScanner(ABC):

    def __init__(self, rules):
        self.rules = rules

    @abstractmethod
    def scan(self, repo_url, **kwargs):
        pass
