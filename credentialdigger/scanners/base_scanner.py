import tempfile
from abc import ABC, abstractmethod

from git import Repo as GitRepo


class BaseScanner(ABC):

    def __init__(self, rules):
        self.rules = rules

    @abstractmethod
    def scan(self, repo_url, **kwargs):
        pass

    def clone_git_repo(self, git_url):
        """ Clone git repository. """
        project_path = tempfile.mkdtemp()
        GitRepo.clone_from(git_url, project_path)
        return project_path
