import os
import shutil
import tempfile
from abc import abstractmethod
from collections import namedtuple

import git
from credentialdigger import Client
from credentialdigger.snippet_similarity import (
    build_embedding_model,
    compute_similarity,
    compute_snippet_embedding)
from git import GitCommandError, InvalidGitRepositoryError, NoSuchPathError
from git import Repo as GitRepo

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
            The query to be run, with placeholders in place of parameters
        params: list
            The parameters to be substituted in the placeholders
        """
        cursor = self.db.cursor()
        cursor.execute(query, tuple(params))
        result = cursor.fetchone()[0]
        return result

    def get_all_discoveries_count(self):
        """ Get the repositories together with their total number of
        discoveries and the number of "new" ones.

        Returns
        -------
        list
            A list of tuples containing (repo_url, total disc, new disc)
        """
        query = '''SELECT repo_url,
                          COUNT(*) as total,
                          sum(case when STATE='new' then 1 else 0 end) as tp
                          FROM discoveries
                          GROUP BY repo_url;'''
        cursor = self.db.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        return result

    def get_files_summary(self, query, repo_url):
        """ Get aggregated discoveries info on all files of a repository.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
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

    def check_repo(self, repo_url, git_token=None, local_repo=False,
                   branch_or_commit=None):
        """ Check git token validity for the repository.

        Parameters
        ----------
        repo_url: str
            The location of a git repository (an url if local_repo is False, a
            local path otherwise)
        git_token: str, optional
            Git personal access token to authenticate to the git server
        local_repo: bool, optional
            If True, get the repository from a local directory instead of the
            web
        branch_or_commit: str
            The branch name or the commit id the repo must be checked out at

        Returns
        -------
        bool
            True if the git token is valid for the repository, False otherwise
        str
            The error raised (`None` if no errors where raised)
        """
        if local_repo:
            try:
                GitRepo(repo_url)
            except InvalidGitRepositoryError:
                return False, 'InvalidGitRepositoryError'
            except NoSuchPathError:
                return False, 'NoSuchPathError'
        else:
            g = git.cmd.Git()
            if git_token is not None and len(git_token) > 0:
                repo_url = repo_url.replace('https://',
                                            f'https://oauth2:{git_token}@')
            try:
                remote_refs = g.ls_remote(repo_url)
                if branch_or_commit and branch_or_commit not in remote_refs:
                    # The branch_or_commit value could be a commit id
                    # that is not in the head/ref/tag of this repository.
                    # So the only way to verify it is to clone the repo and
                    # do a checkout
                    return self._check_repo_commit(repo_url, branch_or_commit)
            except GitCommandError:
                return False, 'GitCommandError'
        return True, None

    def _check_repo_commit(self, repo_url, commit_id, local_repo=False):
        """ Get a git repository.

        TODO: implement local_repo support

        Parameters
        ----------
        repo_url: str
            The location of the git repository (an url if local is False, a
            local path otherwise)
        branch_or_commit: str
            The branch name or the commit id
        local_repo: bool
            If True, get the repository from a local directory instead of the
            web.

        Returns
        -------
        bool
            Whether the repo has been successfully checked out at
            `branch_or_commit`
        str
            The error raised (`None` if no errors where raised)

        Raises
        ------
        FileNotFoundError
            If repo_url is not an existing directory
        git.InvalidGitRepositoryError
            If the directory in repo_url is not a git repository
        git.GitCommandError
            If the url in repo_url is not a git repository, or access to the
            repository is denied
        """
        project_path = tempfile.mkdtemp()
        if local_repo:
            # At the moment, local_repo is not supported and is always set to
            # False
            # TODO: implement and merge this (the following piece of code is
            # copied from git_scanner.get_git_repo)
            # TODO: local_repo are not yet supported. The local_repo value is
            # always set to False (at this moment)
            project_path = os.path.join(tempfile.mkdtemp(), 'repo')
            try:
                shutil.copytree(repo_url, project_path)
                repo = GitRepo(project_path)
                repo.git.checkout(commit_id)
            except FileNotFoundError as e:
                shutil.rmtree(project_path)
                raise e
                # TODO: return the right values instead of raising exception
            except InvalidGitRepositoryError as e:
                shutil.rmtree(project_path)
                raise InvalidGitRepositoryError(
                    f'\"{repo_url}\" is not a local git repository.') from e
                # TODO: return the right values instead of raising exception
        else:
            try:
                GitRepo.clone_from(repo_url, project_path)
                repo = GitRepo(project_path)
                # Checkout this commit (an error is raised if not existing)
                repo.git.checkout(commit_id)
            except GitCommandError:
                shutil.rmtree(project_path)
                return False, 'WrongBranchError'

        return True, None
