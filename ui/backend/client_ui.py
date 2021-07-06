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

    def check_repo(self, repo_url, git_token=None, local_repo=False):
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
                g.ls_remote(repo_url)
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
            State to update similar snippets to
        repo_url: str
        file_name: str
            Restrict to a given file the search for similar snippets
        threshold: float
            Update snippets with similarity score above threshold.
            Values lesser than 0.94 do not generally imply any relevant
            amount of similarity between snippets, and should
            therefore not be used.

        Returns
        -------
        int
            The number of similar snippets found and updated
        """

        discoveries = self.get_discoveries(repo_url, file_name)[1]
        # Compute target snippet embedding
        target_embedding = self.get_embedding(snippet=target_snippet)
        n_updated_snippets = 0
        if not target_embedding:
            return 0
        else:
            for d in discoveries:
                if (
                    d['state'] != state
                    and self.get_embedding(discovery_id=d['id'])
                ):
                    # Compute similarity of target embedding and embedding
                    embedding = self.get_embedding(discovery_id=d['id'])
                    similarity = compute_similarity(target_embedding,
                                                    embedding)
                    if similarity > threshold:
                        n_updated_snippets += 1
                        self.update_discovery(d['id'], state)
            return n_updated_snippets
