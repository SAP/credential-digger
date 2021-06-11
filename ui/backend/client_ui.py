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
    """
    def update_similar_snippets(self,
                                target_snippet,
                                state,
                                repo_url,
                                file_name=None,
                                threshold=0.96):

        discoveries = self.get_discoveries(repo_url,
                                           file_name,
                                           state_filter='new')[1]
        model = build_embedding_model()
        target_snippet_embedding = compute_snippet_embedding(target_snippet,
                                                             model)
        n_updated_snippets = 0
        for d in discoveries:
            #snippet_embedding = compute_snippet_embedding(d['snippet'],
            #                                              model)
            similarity = compute_similarity(target_snippet_embedding,
                                            d['embedding'])
            if similarity > threshold:
                n_updated_snippets += 1
                self.update_discovery(d['id'], state)
        return n_updated_snippets
    """

    def update_similar_snippets(self,
                                target_snippet,
                                state,
                                repo_url,
                                file_name=None,
                                threshold=0.96):
    
        discoveries = self.get_discoveries(repo_url, file_name)[0]
        """ Compute target snippet embedding """
        str_target_discovery_embedding = (self.get_embedding(target_discovery_id))[0].split(",")[:-1]
        target_discovery_embedding = [float(emb) for emb in str_target_discovery_embedding]
        n_updated_snippets = 0
        for d in discoveries:
            if d['state'] != state and self.get_embedding(d['id']):
                """ Compute similarity of target snippet and snippet """
                str_embedding = (self.get_embedding(d['id']))[0].split(",")[:-1]
                embedding = [float(emb) for emb in str_embedding]
                similarity = compute_similarity(target_discovery_embedding, embedding)
                if similarity > threshold:
                    n_updated_snippets += 1
                    self.update_discovery(d['id'], state)
        return n_updated_snippets
