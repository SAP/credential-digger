from abc import abstractmethod
from collections import namedtuple

import git
from credentialdigger import Client
from git import GitCommandError

FilesSummary = namedtuple(
    'FilesSummary',
    'file_name tot_discoveries new false_positives addressing not_relevant')


class UiClient(Client):
    @abstractmethod
    def get_discoveries(self, query, params):
        pass

    def get_discoveries_count(self, query, params):
        """ Get the total number of discoveries.

        Parameters
        ----------
        query: str
            The specific query to run (with placeholders for parameters)
        params: list
            The parameters to be substituted in the placeholders
        """
        cursor = self.db.cursor()
        cursor.execute(query, tuple(params))
        result = cursor.fetchone()[0]
        return result

    def get_files_summary(self, query, repo_url):
        """ Get aggregated discoveries info on all files of a repository.

        Parameters
        ----------
        repo_url: str
            The url of the repository

        Returns
        -------
        list
            A list of files with aggregated data (dictionaries)

        Raises
        ------
            TypeError
                If any of the required arguments is missing
        """
        cursor = self.db.cursor()
        files = []
        cursor.execute(query, (repo_url,))
        result = cursor.fetchone()
        while result:
            files.append(dict(FilesSummary(*result)._asdict()))
            result = cursor.fetchone()
        return files

    def check_connection(self, repo_url, git_token=None):
        """
        Check git token validity for the repository

        Parameters
        ----------
        repo_url: str
            The url of the repository
        git_token: str, optional
            Git personal access token to authenticate to the git server

        Returns
        -------
        bool
            True if the git token is valid for the repository, False otherwise
        """
        g = git.cmd.Git()
        if git_token is not None and len(git_token) > 0:
            repo_url = repo_url.replace('https://',
                                        f'https://oauth2:{git_token}@')
        try:
            g.ls_remote(repo_url)
        except GitCommandError:
            return False
        return True
