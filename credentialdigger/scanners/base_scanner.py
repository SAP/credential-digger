import tempfile
from abc import ABC, abstractmethod

from git import Repo as GitRepo


class BaseScanner(ABC):

    def __init__(self, rules):
        """
        Initialize the rules.

        Args:
            self: (todo): write your description
            rules: (str): write your description
        """
        self.rules = rules

    @abstractmethod
    def scan(self, repo_url, **kwargs):
        """
        Scan a repository.

        Args:
            self: (todo): write your description
            repo_url: (str): write your description
        """
        pass

    def clone_git_repo(self, git_url):
        """ Clone git repository. """
        project_path = tempfile.mkdtemp()
        GitRepo.clone_from(git_url, project_path)
        return project_path
