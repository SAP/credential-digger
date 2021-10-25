import json
import logging
import os
import urllib3
from abc import ABC, abstractmethod
from collections import namedtuple
from datetime import datetime, timezone

import yaml
from github import Github
from rich.progress import Progress

from .models.model_manager import ModelManager
from .scanners.file_scanner import FileScanner
from .scanners.git_file_scanner import GitFileScanner
from .scanners.git_scanner import GitScanner
from .snippet_similarity import (build_embedding_model, compute_similarity,
                                 compute_snippet_embedding)


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

Rule = namedtuple('Rule', 'id regex category description')
Repo = namedtuple('Repo', 'url last_scan')
Discovery = namedtuple(
    'Discovery',
    'id file_name commit_id line_number snippet repo_url rule_id state \
    timestamp')


class Interface(ABC):
    """ Abstract class that simplifies queries for python database module
    that implements Python Database API Specification v2.0 (PEP 249).

    Parameters
    ----------
    db: database class (as defined in Python Database API Specification v2.0
        (PEP 249))
    Error: base exception class for the corresponding database type
    """

    def __init__(self, db, error):
        self.db = db
        self.Error = error

    def query(self, query, *args):
        cursor = self.db.cursor()
        try:
            cursor.execute(query, args)
            self.db.commit()
            return True
        except (TypeError, IndexError):
            # A TypeError is raised if any of the required arguments is missing
            self.db.rollback()
            return False
        except self.Error:
            self.db.rollback()
            return False

    @abstractmethod
    def query_check(self, query, *args):
        return

    @abstractmethod
    def query_id(self, query, *args):
        return

    def query_as(self, query, cast, *args):
        cursor = self.db.cursor()
        try:
            cursor.execute(query, args)
            return dict(cast(*cursor.fetchone())._asdict())
        except (TypeError, IndexError):
            # A TypeError is raised if any of the required arguments is missing
            self.db.rollback()
            return ()
        except self.Error:
            self.db.rollback()
            return ()


class Client(Interface):
    def __init__(self, db, error):
        super().__init__(db, error)

    def add_discovery(self, query, file_name, commit_id, line_number, snippet,
                      repo_url, rule_id, state='new'):
        """ Add a new discovery.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        file_name: str
            The name of the file that produced the discovery
        commit_id: str
            The id of the commit introducing the discovery
        line_number: int
            The line number of the discovery in the file
        snippet: str
            The line matched during the scan
        repo_url: str
            The url of the repository
        rule_id: str
            The id of the rule used during the scan
        state: str, default `new`
            The state of the discovery

        Returns
        -------
        int
            The id of the new discovery (-1 in case of error)
        """
        return self.query_id(
            query, file_name,
            commit_id, line_number, snippet,
            repo_url, rule_id, state)

    @abstractmethod
    def add_discoveries(self, query, discoveries, repo_url):
        return

    def add_embedding(self, query, discovery_id, repo_url, embedding=None):
        """ Add an embedding to the embeddings table.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        discovery_id: int
            The id of the discovery whose embedding is to be added
        snippet: str
            The snippet whose embedding is to be added
        repo_url: str
            The discovery's repository url
        embedding: list
            The embedding to be added
        """
        snippet = self.get_discovery(discovery_id)['snippet']
        if not embedding:
            # We have to compute the embedding for this snippet
            global similarity_model
            similarity_model = globals().get('similarity_model')
            # If the similarity model has not been computed yet, we have to do
            # it now. We also keep it in the global variables in order not to
            # compute it every time (it can be time consuming)
            if not similarity_model:
                similarity_model = build_embedding_model()
            embedding = compute_snippet_embedding(snippet,
                                                  similarity_model)
        embedding = json.dumps(embedding)
        cursor = self.db.cursor()
        try:
            cursor.execute(query, (discovery_id,
                                   snippet,
                                   embedding,
                                   repo_url))
            self.db.commit()
        except self.Error:
            self.db.rollback()

    def add_embeddings(self, query, repo_url):
        """ Bulk add embeddings to the embeddings table.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        repo_url: str
            The repository url
        """
        [discoveries_ids,
         snippets,
         embeddings] = self.compute_repo_embeddings(repo_url)
        embedding_strings = list(map(json.dumps, embeddings))

        cursor = self.db.cursor()
        try:
            insert_tuples = list(zip(discoveries_ids,
                                     snippets,
                                     embedding_strings,
                                     [repo_url] * len(discoveries_ids)))
            cursor.executemany(query, insert_tuples)
            self.db.commit()
        except self.Error:
            self.db.rollback()

    def add_repo(self, query, repo_url):
        """ Add a new repository.

        Do not set the latest commit (it will be set when the repository is
        scanned).

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        repo_url: str
            The url of the repository

        Returns
        -------
        bool
            `True` if the insert was successfull, `False` otherwise
        """
        return self.query(query, repo_url,)

    def add_rule(self, query, regex, category, description=''):
        """ Add a new rule.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        regex: str
            The regex to be matched
        category: str
            The category of the rule
        description: str, optional
            The description of the rule

        Returns
        -------
        int
            The id of the new rule (-1 in case of errors)
        """
        return self.query_id(query, regex, category, description)

    def add_rules_from_file(self, filename):
        """ Add rules from a file.

        Parameters
        ----------
        filename: str
            The file containing the rules

        Raises
        ------
        FileNotFoundError
            If the file does not exist
        ParserError
            If the file is malformed
        KeyError
            If one of the required attributes in the file (i.e., rules, regex,
            and category) is missing
        """
        with open(filename, 'r') as f:
            data = yaml.safe_load(f)
        for rule in data['rules']:
            self.add_rule(rule['regex'],
                          rule['category'],
                          rule.get('description', ''))

    def delete_rule(self, query, ruleid):
        """Delete a rule from database

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        ruleid: int
            The id of the rule that will be deleted.

        Returns
        ------
        False
            If the removal operation fails
        True
            Otherwise
        """
        cursor = self.db.cursor()
        try:
            cursor.execute(query, (ruleid,))
            self.db.commit()
            return bool(cursor.fetchone()[0])
        except (TypeError, IndexError):
            # A TypeError is raised if any of the required arguments is missing
            self.db.rollback()
            return False
        except self.Error:
            self.db.rollback()
            return False
        return True

    def delete_repo(self, query, repo_url):
        """ Delete a repository.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        repo_url: str
            The url of the repository to delete

        Returns
        -------
        bool
            `True` if the repo was successfully deleted, `False` otherwise
        """
        return self.query(query, repo_url,)

    def delete_discoveries(self, query, repo_url):
        """ Delete all discoveries of a repository.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        repo_url: str
            The repository url of the discoveries to delete

        Returns
        -------
        bool
            `True` if the discoveries were successfully deleted, `False`
            otherwise
        """
        return self.query(query, repo_url,)

    def delete_embedding(self, query, discovery_id):
        """ Delete an embedding.

        Parameters
        ----------
        query: str
            The query to be run
        discovery_id: int
            The id of the discovery whose embedding is
            to be deleted

        Returns
        -------
        bool
            `True` if embedding was successfully deleted,
            `False` otherwise
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(query, discovery_id)
            self.db.commit()
            return True
        except self.Error:
            self.db.rollback()
            return False

    def delete_embeddings(self, query, repo_url):
        """ Bulk delete embeddings.

        Parameters
        ----------
        query: str
            The query to be run
        repo_url: str
            The url of the repository whose embeddings are
            to be deleted

        Returns
        -------
        bool
            `True` if embeddings were successfully deleted,
            `False` otherwise
        """
        try:
            cursor = self.db.cursor()
            cursor.execute(query, (repo_url,))
            self.db.commit()
            return True
        except self.Error:
            self.db.rollback()
            return False

    def get_repos(self):
        """ Get all the repositories.

        Returns
        -------
        list
            A list of repositories (dictionaries).
            An empty list if there are no repos (or in case of errors)

        Raises
        ------
        TypeError
            If any of the required arguments is missing
        """
        query = 'SELECT * FROM repos'
        cursor = self.db.cursor()
        all_repos = []
        cursor.execute(query)
        result = cursor.fetchone()
        while result:
            all_repos.append(dict(Repo(*result)._asdict()))
            result = cursor.fetchone()
        return all_repos

    def get_repo(self, query, repo_url):
        """ Get a repository.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        repo_url: str
            The url of the repository

        Returns
        -------
        dict
            A repository (an empty dictionary if the url does not exist)

        Raises
        ------
        TypeError
            If any of the required arguments is missing
        """
        cursor = self.db.cursor()
        cursor.execute(query, (repo_url,))
        result = cursor.fetchone()
        if result:
            return dict(Repo(*result)._asdict())
        else:
            return {}

    def get_rules(self, category_query=None, category=None):
        """ Get the rules.

        Differently from other get methods, here we pass the category as
        argument. This is due to the fact that categories may have a slash
        (e.g., `auth/password`). Encoding such categories in the url would
        cause an error on the server side.

        NOTE: Here exceptions are suppressed in order to not stop the scanning.

        Parameters
        ----------
        category_query: str, optional
            If specified, run this specific query (with `category` as an
            argument), otherwise get all the rules
        category: str, optional
            If specified get all the rules of this category, otherwise get all
            the rules

        Returns
        -------
        list
            A list of rules (dictionaries)
        """
        query = 'SELECT * FROM rules'
        if category_query is not None and category is not None:
            query = category_query
        cursor = self.db.cursor()
        try:
            all_rules = []

            if category is not None:
                cursor.execute(query, (category,))
            else:
                cursor.execute(query)

            result = cursor.fetchone()
            while result:
                all_rules.append(dict(Rule(*result)._asdict()))
                result = cursor.fetchone()
            return all_rules
        except (TypeError, IndexError):
            # A TypeError is raised if any of the required arguments is missing
            self.db.rollback()
            return []
        except self.Error:
            self.db.rollback()
            return []

    def get_rule(self, query, rule_id):
        """ Get a rule.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        rule_id: int
            The id of the rule

        Returns
        -------
        dict
            A rule
        """
        return self.query_as(query, Rule, rule_id,)

    def get_discoveries(self, query, repo_url, file_name=None):
        """ Get all the discoveries of a repository.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        repo_url: str
            The url of the repository
        file_name: str, optional
            The name of the file to filter discoveries on

        Returns
        -------
        list
            A list of discoveries (dictionaries)

        Raises
        ------
        TypeError
            If any of the required arguments is missing
        """
        cursor = self.db.cursor()
        all_discoveries = []
        params = (repo_url,) if file_name is None else (
            repo_url, file_name)
        cursor.execute(query, params)
        result = cursor.fetchone()
        while result:
            all_discoveries.append(dict(Discovery(*result)._asdict()))
            result = cursor.fetchone()
        return all_discoveries

    def get_discovery(self, query, discovery_id):
        """ Get a discovery.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        discovery_id: int
            The id of the discovery

        Returns
        -------
        dict
            A discovery
        """
        return self.query_as(query, Discovery, discovery_id,)

    def get_discovery_group(self, query, state_query, repo_url, state=None):
        """ Get all the discoveries of a repository, grouped by file_name,
        snippet, and state.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        repo_url: str
            The url of the repository
        state: str, optional
            The state of the discoveries. If not set, get all the discoveries
            independently from their state

        Returns
        -------
        list
            A list of tuples. Each tuple is composed by file_name, snippet,
            number of times that this couple occurs, and the state of the
            couple.

        Raises
        ------
        TypeError
            If any of the required arguments is missing
        """
        cursor = self.db.cursor()
        if state is not None:
            cursor.execute(state_query, (repo_url, state))
        else:
            cursor.execute(query, (repo_url,))
        return cursor.fetchall()

    def get_embedding(self, query, discovery_id=None, snippet=None):
        """ Retrieve a discovery embedding.

        This method retrieves the embedding of the discovery whose id is
        passed as argument.
        If no id is provided, the method retrieves the embedding of
        the arguments' snippet.
        If the snippet is missing as well, None is returned.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        discovery_id: int, optional
            The id of the discovery whose embedding is being retrieved
        snippet: str, optional
            The snippet whose embedding is being retrieved. Only used if
            discovery_id is not provided

        Returns
        -------
        list
            The embedding for the provided snippet or id
        """
        cursor = self.db.cursor()
        try:
            if discovery_id:
                cursor.execute(query, (discovery_id,))
            elif snippet:
                cursor.execute(query, (snippet,))
            else:
                return None
            embedding_str = cursor.fetchone()[0]
            return json.loads(embedding_str)
        except TypeError:
            # The embedding tuple was empty when fetched
            return None
        except self.Error:
            return None

    def get_embeddings(self, query, repo_url):
        """ Retrieve embeddings for an entire repository.

        Parameters
        ----------
        query: str
            The query to be run
        repo_url: str
            The repository url

        Returns
        -------
        dictionary
            A dictionary with discovery ids as keys and matching
            embeddings (i.e., a list of floats) as values
        """
        cursor = self.db.cursor()
        try:
            cursor.execute(query, (repo_url,))
            embeddings_tuples = cursor.fetchall()
        except self.Error:
            return None

        return dict((emb_id, json.loads(emb_str)) for emb_id, emb_str in
                    embeddings_tuples)

    def update_repo(self, query, url, last_scan):
        """ Update the last scan timestamp of a repo.

        After a scan, record the timestamp of the last scan, such that
        another (future) scan will not process the same commits twice.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        url: str
            The url of the repository scanned
        last_scan: int
            The timestamp of the last scan

        Returns
        -------
        bool
            `True` if the update is successful, `False` otherwise
        """
        return self.query_check(query, last_scan, url)

    def update_discovery(self, query, discovery_id, new_state):
        """ Change the state of a discovery.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        discovery_id: int
            The id of the discovery to be updated
        new_state: str
            The new state of this discovery

        Returns
        -------
        bool
            `True` if the update is successful, `False` otherwise
        """
        if new_state not in ('new', 'false_positive', 'addressing',
                             'not_relevant', 'fixed'):
            return False

        return self.query_check(query, new_state, discovery_id)

    def update_discoveries(self, query, discoveries_ids, new_state):
        """ Change the state of multiple discoveries.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        discoveries_ids: list
            The ids of the discoveries to be updated
        new_state: str
            The new state of these discoveries

        Returns
        -------
        bool
            `True` if the update is successful, `False` otherwise
        """
        if new_state not in ('new', 'false_positive', 'addressing',
                             'not_relevant', 'fixed'):
            return False

        return self.query_check(query, new_state, tuple(discoveries_ids))

    def update_discovery_group(self, query, new_state, repo_url,
                               file_name=None, snippet=None):
        """ Change the state of a group of discoveries.

        A group of discoveries is identified by the url of their repository,
        their filename, and their snippet.

        Parameters
        ----------
        query: str
            The query to be run, with placeholders in place of parameters
        new_state: str
            The new state of these discoveries
        repo_url: str
            The url of the repository
        file_name: str, optional
            The name of the file
        snippet: str, optional
            The snippet

        Returns
        -------
        bool
            `True` if the update is successful, `False` otherwise
        """
        if new_state not in ('new', 'false_positive', 'addressing',
                             'not_relevant', 'fixed'):
            return False
        if not snippet:
            return self.query_check(query, new_state, repo_url, file_name)
        elif not file_name:
            return self.query_check(query, new_state, repo_url, snippet)
        else:
            return self.query_check(
                query, new_state, repo_url, file_name, snippet)

    def scan(self, repo_url, category=None, models=None, force=False,
             debug=False, similarity=False, local_repo=False,
             git_username=None, git_token=None):
        """ Launch the scan of a git repository.

        Parameters
        ----------
        repo_url: str
            The url of the repo to scan
        category: str, optional
            If specified, scan the repo using all the rules of this category,
            otherwise use all the rules in the db
        models: list, optional
            A list of models for the ML false positives detection
        force: bool, default `False`
            Force a complete re-scan of the repository, in case it has already
            been scanned previously
        debug: bool, default `False`
            Flag used to decide whether to visualize the progressbars during
            the scan (e.g., during the insertion of the detections in the db)
        similarity: bool, default `False`
            Decide whether to build the embedding model and to compute and add
            embeddings, to allow for updating of similar discoveries
        local_repo: bool, optional
            If True, get the repository from a local directory instead of the
            web
        git_username: str, optional
            the username of the user to authenticate to the git server
        git_token: str, optional
            Git personal access token to authenticate to the git server

        Returns
        -------
        list
            The id of the discoveries detected by the scanner (excluded the
            ones classified as false positives).
        """
        if local_repo:
            repo_url = os.path.abspath(repo_url)
        else:
            # Trim the tail of the repo's url by removing '/' and '.git'
            if repo_url.endswith('/'):
                repo_url = repo_url[:-1]
            if repo_url.endswith('.git'):
                repo_url = repo_url[:-4]

        rules = self._get_scan_rules(category)
        scanner = GitScanner(rules)

        return self._scan(
            repo_url=repo_url, scanner=scanner, models=models, force=force,
            debug=debug, similarity=similarity, local_repo=local_repo,
            git_username=git_username, git_token=git_token)

    def scan_snapshot(self, repo_url, branch_or_commit, category=None,
                      models=None, force=False, debug=False, similarity=False,
                      git_username=None, git_token=None, max_depth=-1,
                      ignore_list=[]):
        """ Launch the scan of the snapshot of a git repository.
        This scan mode takes into consideration the snapshot of the repository
        at one specific commit, or at the last commit of a specific branch.

        Parameters
        ----------
        repo_url: str
            The url of the repo to scan
        branch_or_commit: str
            The commit hash or the branch name
        category: str, optional
            If specified, scan the repo using all the rules of this category,
            otherwise use all the rules in the db
        models: list, optional
            A list of models for the ML false positives detection
        force: bool, default `False`
            Force a complete re-scan of the repository, in case it has already
            been scanned previously
        debug: bool, default `False`
            Flag used to decide whether to visualize the progressbars during
            the scan (e.g., during the insertion of the detections in the db)
        git_username: str, optional
            the username of the user to authenticate to the git server
        git_token: str, optional
            Git personal access token to authenticate to the git server
        max_depth: int, optional
            The maximum depth to which traverse the subdirectories tree.
            A negative value will not affect the scan.
        ignore_list: list, optional
            A list of paths to ignore during the scan. This can include file
            names, directory names, or whole paths. Wildcards are supported as
            per the fnmatch package.

        Returns
        -------
        list
            The id of the discoveries detected by the scanner (excluded the
            ones classified as false positives).
        """
        if self.get_repo(repo_url) != {}:
            logger.info(f'The repository \"{repo_url}\" has already been '
                        'scanned.')
            if force:
                logger.info('It will be rescanned (old discoveries will be '
                            'deleted) due to force=True')
            else:
                logger.info('Only the diff with the previous scan will be '
                            'considered')

        rules = self._get_scan_rules(category)
        scanner = GitFileScanner(rules)

        return self._scan(
            repo_url=repo_url, branch_or_commit=branch_or_commit,
            scanner=scanner, models=models, force=force, debug=debug,
            similarity=similarity, git_username=git_username,
            git_token=git_token, max_depth=max_depth,
            ignore_list=ignore_list)

    def scan_path(self, scan_path, category=None, models=None, force=False,
                  debug=False, similarity=False, max_depth=-1, ignore_list=[]):
        """ Launch the scan of a local directory or file.

        Parameters
        ----------
        scan_path: str
            The path of the directory or file to scan
        category: str, optional
            If specified, scan the repo using all the rules of this category,
            otherwise use all the rules in the db
        models: list, optional
            A list of models for the ML false positives detection
        force: bool, default `False`
            Force a complete re-scan of the repository, in case it has already
            been scanned previously
        debug: bool, default `False`
            Flag used to decide whether to visualize the progressbars during
            the scan (e.g., during the insertion of the detections in the db)
        max_depth: int, optional
            The maximum depth to which traverse the subdirectories tree.
            A negative value will not affect the scan.
        ignore_list: list, optional
            A list of paths to ignore during the scan. This can include file
            names, directory names, or whole paths. Wildcards are supported as
            per the fnmatch package.

        Returns
        -------
        list
            The id of the discoveries detected by the scanner (excluded the
            ones classified as false positives).
        """
        scan_path = os.path.abspath(scan_path)

        if self.get_repo(scan_path) != {} and force is False:
            raise ValueError(f'The directory \"{scan_path}\" has already been '
                             'scanned. Please use \"force\" to rescan it.')

        rules = self._get_scan_rules(category)
        scanner = FileScanner(rules)

        return self._scan(
            repo_url=scan_path, scanner=scanner, models=models, force=force,
            debug=debug, similarity=similarity, max_depth=max_depth,
            ignore_list=ignore_list)

    def scan_user(self, username, category=None, models=None, debug=False,
                  forks=False, similarity=False, git_token=None,
                  api_endpoint='https://api.github.com'):
        """ Scan all the repositories of a user.

        Find all the repositories of a user, and scan
        them. Please note that git limits the list of repositories to maximum
        100 (due to pagination).

        Parameters
        ----------
        username: str
            The username as on github.com
        category: str, optional
            If specified, scan the repo using all the rules of this category,
            otherwise use all the rules in the db
        models: list, optional
            A list of models for the ML false positives detection
        debug: bool, default `False`
            Flag used to decide whether to visualize the progressbars during
            the scan (e.g., during the insertion of the detections in the db)
        forks: bool, default `False`
            Scan also repositories forked by this user
        git_token: str, optional
            Git personal access token to authenticate to the git server
        api_endpoint: str, default `https://api.github.com`
            API endpoint of the git server (default is github.com)

        Returns
        -------
        dict
            The id of the discoveries detected by the scanner (excluded the
            ones classified as false positives), grouped by repository.
        """
        # Disable warnings due to verify=false at login
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        logger.debug(f'Use API endpoint {api_endpoint}')

        rules = self._get_scan_rules(category)
        scanner = GitScanner(rules)

        g = Github(base_url=api_endpoint,
                   login_or_token=git_token,
                   verify=False)
        missing_ids = {}

        if g.get_user().login == username:
            # Get the repos of the currently authenticated user
            # The API for get_user(username) will return only the public
            # repositories for that user, so it's not suitable to scan all the
            # repos (private ones included) of the authenticated user
            repositories = g.get_user().get_repos(affiliation='owner')
            logger.debug('Scan repos of currently token-authenticated user')
        else:
            user = g.get_user(username)
            if user.type == 'Organization':
                # If this is an org, we have to change API call
                user = g.get_organization(username)
                logger.debug('Scan repos of an organization')
            repositories = user.get_repos()
        repos_num = repositories.totalCount

        i = 0
        for repo in repositories:
            i += 1
            if not forks and repo.fork:
                # Ignore this repo since it is a fork
                logger.info(f'{i}/{repos_num}) Ignore {repo} (it is a fork)')
                continue
            # Get repo clone url without .git at the end
            repo_url = repo.clone_url[:-4]
            logger.info(f'{i}/{repos_num}) Scanning {repo.url}')
            missing_ids[repo_url] = self._scan(repo_url, scanner,
                                               models=models,
                                               debug=debug,
                                               similarity=similarity,
                                               git_token=git_token)
        return missing_ids

    def scan_wiki(self, repo_url, category=None, models=None, debug=False,
                  git_token=None):
        """ Scan the wiki of a repository.

        This method simply generates the url of a wiki from the url of its
        repo, and uses the same `scan` method that we use for repositories.

        Parameters
        ----------
        repo_url: str
            The url of the repository
        category: str, optional
            If specified, scan the repo using all the rules of this category,
            otherwise use all the rules in the db
        models: list, optional
            A list of models for the ML false positives detection
        debug: bool, default `False`
            Flag used to decide whether to visualize the progressbars during
            the scan (e.g., during the insertion of the detections in the db)
        git_token: str, optional
            Git personal access token to authenticate to the git server

        Returns
        -------
        list
            The id of the discoveries detected by the scanner (excluded the
            ones classified as false positives).
        """
        rules = self._get_scan_rules(category)
        scanner = GitScanner(rules)

        # The url of a wiki is same as the url of its repo, but ending with
        # `.wiki.git`
        return self._scan(repo_url + '.wiki.git', scanner, models=models,
                          debug=debug, force=True, git_token=git_token)

    def _scan(self, repo_url, scanner, models=None, force=False, debug=False,
              similarity=False, **scanner_kwargs):
        """ Launch the scan of a repository.

        Parameters
        ----------
        repo_url: str
            The location of a git repository (either an url or a local path,
            depending on the scanner)
        scanner: `scanners.BaseScanner`
            The instance of the scanner, a subclass of `scanners.BaseScanner`
        models: list, optional
            A list of models for the ML false positives detection
        force: bool, default `False`
            Force a complete re-scan of the repository, in case it has already
            been scanned previously
        debug: bool, default `False`
            Flag used to decide whether to visualize the progressbars during
            the scan (e.g., during the insertion of the detections in the db)
        similarity: bool, default `False`
            Decide whether to build the embedding model and to compute and add
            embeddings, to allow for updating of similar discoveries
        scanner_kwargs: kwargs
            Keyword arguments to be passed to the scanner

        Returns
        -------
        list
            The id of the discoveries detected by the scanner (excluded the
            ones classified as false positives).
        """
        if debug:
            logger.setLevel(level=logging.DEBUG)

        if models is None:
            logger.debug('Don\'t use ML models')
            models = []

        # Try to add the repository to the db
        if self.add_repo(repo_url):
            # The repository is new, scan from the first commit
            from_timestamp = 0
            new_repo = True
        else:
            # Get the latest commit recorded on the db
            # `or` clause needed in case the previous scan attempt was broken
            from_timestamp = self.get_repo(repo_url)['last_scan'] or 0
            new_repo = False

        # Force complete scan
        if force:
            logger.debug('Force complete scan')
            self.delete_discoveries(repo_url)
            from_timestamp = 0

        # Call scanner
        scanner_kwargs['since_timestamp'] = from_timestamp
        try:
            logger.debug('Start scan')
            new_discoveries = scanner.scan(repo_url,
                                           debug=debug,
                                           **scanner_kwargs)
            logger.info(f'Detected {len(new_discoveries)} discoveries.')
        except Exception as e:
            # Remove the newly added repo before bubbling the error
            if new_repo:
                self.delete_repo(repo_url)
            raise e

        # Update latest scan timestamp of the repo
        latest_timestamp = int(datetime.now(timezone.utc).timestamp())
        if scanner_kwargs.get('branch_or_commit'):
            # Set the last_scan timestamp to the timestamp of this commit
            # In case there is a `branch_or_commit` in the kwargs of the
            # scanner, then the user requested to scan a snapshot.
            # In this case, we need to set the scan time (i.e., the `last_scan`
            # attribute of the repo in the db) to this timestamp not to lose
            # discoveries in case of future non-forced re-scans
            latest_timestamp = scanner.get_commit_timestamp(
                repo_url=repo_url,
                branch_or_commit=scanner_kwargs['branch_or_commit'],
                git_username=scanner_kwargs.get('git_username', None),
                git_token=scanner_kwargs.get('git_token', None))
        self.update_repo(repo_url, latest_timestamp)

        # Analyze each new discovery. If it is classified as false positive,
        # update it in the list
        if len(new_discoveries) > 0:
            for model in models:
                try:
                    mm = ModelManager(model)
                    if model != 'PasswordModel':
                        # If the model is not PasswordModel, we can run it over
                        # all the discoveries
                        self._analyze_discoveries(mm, new_discoveries, debug)
                        continue

                    # The password model can be run only over password
                    # discoveries, i.e., discoveries whose rule_id is a rule
                    # labeled with a "password" category
                    rules = self.get_rules()
                    password_rules = set([
                        r['id'] for r in rules if r['category'] == 'password'])
                    password_discoveries = []
                    no_password_discoveries = []
                    for d in new_discoveries:
                        if d['rule_id'] in password_rules:
                            password_discoveries.append(d)
                        else:
                            no_password_discoveries.append(d)
                    logger.debug('Run the PasswordModel on'
                                 f'{len(password_discoveries)} out of'
                                 f'{len(new_discoveries)} discoveries')
                    # Run the model only on password_discoveries
                    self._analyze_discoveries(mm, password_discoveries, debug)
                    # Restore the new_discoveries list for the next model,
                    # re-joining the password discoveries and the non-password
                    # ones
                    new_discoveries = password_discoveries + \
                        no_password_discoveries

                except ModuleNotFoundError:
                    logger.warning(f'Model {model} not found. Skip it.')
                    continue

        # Insert the discoveries into the db
        discoveries_ids = list()
        if debug:
            logger.debug('Update database with these discoveries.')
            with Progress() as progress:
                inserting_task = progress.add_task('Inserting discoveries...',
                                                   total=len(new_discoveries))
                for curr_d in new_discoveries:
                    new_id = self.add_discovery(
                        curr_d['file_name'], curr_d['commit_id'],
                        curr_d['line_number'], curr_d['snippet'], repo_url,
                        curr_d['rule_id'], curr_d['state'])
                    if new_id != -1 and curr_d['state'] != 'false_positive':
                        discoveries_ids.append(new_id)
                    progress.update(inserting_task, advance=1)
        else:
            # IDs of the discoveries added to the db
            discoveries_ids = self.add_discoveries(new_discoveries, repo_url)
            discoveries_ids = [
                d for i, d in enumerate(discoveries_ids) if d != -1
                and new_discoveries[i]['state'] != 'false_positive']
        logger.info(f'{len(discoveries_ids)} discoveries left for manual '
                    'review.')

        if similarity and len(discoveries_ids) > 0:
            # Compute similarities only if there are any discoveries left
            logger.info('Compute embeddings for this repository')
            self.add_embeddings(repo_url)
            logger.debug('Done')

        return discoveries_ids

    def _analyze_discoveries(self, model_manager, discoveries, debug):
        """ Launch model and return discoveries with states updated.

        Parameters
        ----------
        model_manager: ModelManager
           The model manager
        discoveries: list
            The discoveries to feed to the model
        debug: boolean
            If true print model name and number of false positives detected

        Return
        ------
        discoveries: list
            The discoveries with states updated according to model predictions
        """

        def _analyze_discovery(this_discovery):
            if this_discovery['state'] == 'new' and \
                    model_manager.launch_model(this_discovery):
                this_discovery['state'] = 'false_positive'
                return 1
            return 0

        if debug:
            model_name = model_manager.model.__class__.__name__
            logger.debug(f'Analyzing discoveries with model {model_name}')
            false_positives = 0
            with Progress() as progress:
                scanning_task = progress.add_task('Scanning discoveries...',
                                                  total=len(discoveries))
                for curr_discovery in discoveries:
                    false_positives += _analyze_discovery(curr_discovery)
                    progress.update(scanning_task, advance=1)
            logger.debug(f'Model {model_name} classified {false_positives} '
                         'discoveries.')
        else:
            # If we don't have to show debug info, we can process all the
            # discoveries in batch
            model_manager.launch_model_batch(discoveries)

        # Return updated discoveries
        return discoveries

    def _get_scan_rules(self, category=None):
        """ Get the rules of the `category`

        Parameters
        ----------
        category: str, optional
            If specified, scan the repo using all the rules of this category,
            otherwise use all the rules in the db

        Returns
        -------
        list
            A list of rules

        Raises
        ------
        ValueError
            If no rules are found or all rules have been filtered out
        """
        rules = self.get_rules(category)
        if not rules:
            raise ValueError('No rules found')

        return rules

    def compute_repo_embeddings(self, repo_url):
        """ Compute embeddings for all discoveries in a repository.

        Parameters
        ----------
        repo_url: str
            The repository url

        Returns
        -------
        list
            A list comprising three lists: the repository's discovery
            ids, snippets, and embeddings
        """
        disc = self.get_discoveries(repo_url)
        # If called by UI classes, disc is a tuple of 2 elements, and the
        # actual discoveries are at the second element (the first one contains
        # the number of discoveries, so, it's an int)
        discoveries = disc[1] if disc and isinstance(disc[0], int) else disc
        discoveries_ids = [d['id'] for d in discoveries]
        snippets = [d['snippet'] for d in discoveries]

        global similarity_model
        similarity_model = globals().get('similarity_model')
        # If the similarity model has not been computed yet, we have to do
        # it now. We also keep it in the global variables in order not to
        # compute it every time (it can be time consuming)
        if not similarity_model:
            similarity_model = build_embedding_model()

        embeddings = [compute_snippet_embedding(s, similarity_model)
                      for s in snippets]
        return [discoveries_ids, snippets, embeddings]

    def update_similar_snippets(self,
                                target_snippet,
                                state,
                                repo_url,
                                file_name=None,
                                compute_missing_embeddings=False,
                                threshold=0.96):
        """ Find snippets that are similar to the target
        snippet and update their state.

        Parameters
        ----------
        target_snippet: str
            The target snippet
        state: str
            State to update similar snippets to
        repo_url: str
            The url of the repository
        file_name: str
            Restrict to a given file the search for similar snippets
        compute_missing_embeddings: bool
            (default `False`)
            Compute (or not) embeddings when they are missing from the db
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
        disc = self.get_discoveries(repo_url, file_name)
        # Discoveries are the second element of the output of
        # get_discoveries in the UI clients, but are the entire
        # output in regular clients
        # (not the elegant way to do it, but hack for double inheritance)
        discoveries = disc[1] if len(disc) == 2 else disc
        # Keep only the discoveries with a state different from the one
        # passed as argument (same state discoveries will not be updated)
        discoveries = filter(lambda d: d['state'] != state, discoveries)

        # Get the embedding of the target snippet
        target_embedding = self.get_embedding(snippet=target_snippet)
        # Get all embeddings for this repo
        all_embeddings = self.get_embeddings(repo_url=repo_url)
        # Check if need to recompute embeddings
        if not all_embeddings and compute_missing_embeddings:
            logger.info(f'Compute embeddings for repo {repo_url}')
            self.add_embeddings(repo_url)
            all_embeddings = self.get_embeddings(repo_url=repo_url)
            if not target_embedding:
                # It may have just been computed
                target_embedding = self.get_embedding(snippet=target_snippet)

        # If the target snippet is not found in the embeddings table, or if
        # the other embeddings are missing, no update is performed
        if not target_embedding or not all_embeddings:
            logger.debug('No embeddings found')
            return 0

        n_updated_snippets = 0
        for d in discoveries:
            embedding = all_embeddings.get(d['id'])
            if not embedding and compute_missing_embeddings:
                # Recompute it
                logger.debug(f'Compute embedding for discovery {d["id"]}')
                self.add_embedding(discovery_id=d['id'], repo_url=repo_url)
                embedding = self.get_embedding(discovery_id=d['id'])
            if not embedding:
                continue
            # Compute similarity of target_embedding and embedding
            similarity = compute_similarity(target_embedding,
                                            embedding)
            if similarity > threshold:
                self.update_discovery(d['id'], state)
                n_updated_snippets += 1
        return n_updated_snippets
