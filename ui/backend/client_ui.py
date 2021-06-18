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
        """
        Check git token validity for the repository

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
            TODO

        Returns
        -------
        bool
            True if the git token is valid for the repository, False otherwise
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
                    # TODO
                    pass
            except GitCommandError:
                return False, 'GitCommandError'
        return True, None

    def update_similar_snippets(self,
                                target_snippet,
                                state,
                                repo_url,
                                file_name=None,
                                threshold=0.96):
        """ Find snippets that are similar to the target
        snippet and update their state.

        Parameters
        ----------
        target_snippet: str
        state: str
            state to update similar snippets to
        repo_url: str
        file_name: str
            restrict to a given file the search for similar snippets
        threshold: float
            update snippets with similarity score above threshold.
            Values lesser than 0.94 do not generally imply any relevant
            amount of similarity between snippets, and should
            therefore not be used.

        Returns
        -------
        int
            The number of similar snippets found and updated
        """

        discoveries = self.get_discoveries(repo_url,
                                           file_name,
                                           state_filter='new')[1]
        model = build_embedding_model()
        target_snippet_embedding = compute_snippet_embedding(target_snippet,
                                                             model)
        n_updated_snippets = 0
        for d in discoveries:
            snippet_embedding = compute_snippet_embedding(d['snippet'],
                                                          model)
            similarity = compute_similarity(target_snippet_embedding,
                                            snippet_embedding)
            if similarity > threshold:
                n_updated_snippets += 1
                self.update_discovery(d['id'], state)
        return n_updated_snippets
