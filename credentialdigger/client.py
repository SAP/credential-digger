import logging
from abc import ABC, abstractmethod
from collections import namedtuple

import yaml
from github import Github
from tqdm import tqdm

from .generator import ExtractorGenerator
from .models.model_manager import ModelManager
from .scanners.git_scanner import GitScanner

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

Rule = namedtuple('Rule', 'id regex category description')
Repo = namedtuple('Repo', 'url last_scan')
Discovery = namedtuple(
    'Discovery',
    'id file_name commit_id line_number snippet repo_url rule_id state timestamp')


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
            """ A TypeError is raised if any of the required arguments is
            missing. """
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
            """ A TypeError is raised if any of the required arguments is
            missing. """
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
            commit_id, line_number, snippet, repo_url, rule_id, state)

    @abstractmethod
    def add_discoveries(self, query, discoveries, repo_url):
        return

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
            """ A TypeError is raised if any of the required arguments is
            missing. """
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
        repo_id: int
            The id of the repo to delete

        Returns
        -------
        bool
            `True` if the repo was successfully deleted, `False` otherwise
        """
        return self.query(query, repo_url,)

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
            The url of the repo

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
            """ A TypeError is raised if any of the required arguments is
            missing. """
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

    def update_discovery_group(self, query, new_state, repo_url, file_name=None,
                               snippet=None):
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
        file_name: str
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
        if snippet is None:
            return self.query_check(query, new_state, repo_url, file_name)
        elif file_name is None:
            return self.query_check(query, new_state, repo_url, snippet)
        else:
            return self.query_check(
                query, new_state, repo_url, file_name, snippet)

    def scan(self, repo_url, category=None, scanner=GitScanner,
             models=None, exclude=None, force=False, debug=False,
             generate_snippet_extractor=False, git_token=None):
        """ Launch the scan of a repository.

        Parameters
        ----------
        repo_url: str
            The url of the repo to scan
        category: str, optional
            If specified, scan the repo using all the rules of this category,
            otherwise use all the rules in the db
        scanner: class, default: `GitScanner`
            The class of the scanner, a subclass of `scanners.BaseScanner`
        models: list, optional
            A list of models for the ML false positives detection
        exclude: list, optional
            A list of rules to exclude
        force: bool, default `False`
            Force a complete re-scan of the repository, in case it has already
            been scanned previously
        debug: bool, default `False`
            Flag used to decide whether to visualize the progressbars during
            the scan (e.g., during the insertion of the detections in the db)
        generate_snippet_extractor: bool, default `False`
            Generate the extractor model to be used in the SnippetModel. The
            extractor is generated using the ExtractorGenerator. If `False`,
            use the pre-trained extractor model
        git_token: str, optional
            Git personal access token to authenticate to the git server

        Returns
        -------
        list
            The id of the discoveries detected by the scanner (excluded the
            ones classified as false positives).
        """
        if debug:
            logger.setLevel(level=logging.DEBUG)

        def analyze_discoveries(model_manager, discoveries, debug):
            """ Use a model to analyze a list of discoveries. """
            false_positives = 0

            # Analyze all the discoveries ids with the current model
            if debug:
                logger.debug(
                    f'Analyzing discoveries with model {model_manager.model}')
                for i in tqdm(range(len(discoveries))):
                    if (discoveries[i]['state'] != 'false_positive' and
                            model_manager.launch_model(discoveries[i])):
                        discoveries[i]['state'] = 'false_positive'
                        false_positives += 1
            else:
                for d in discoveries:
                    if (d['state'] != 'false_positive' and
                            model_manager.launch_model(d)):
                        d['state'] = 'false_positive'
                        false_positives += 1

            if debug:
                logger.debug(
                    f'Model {model_manager.model.__class__.__name__} '
                    f'classified {false_positives} discoveries.')
                logger.debug('Change state to these discoveries')

            # Return updated discoveries
            return discoveries

        if models is None:
            models = []
        if exclude is None:
            exclude = []

        # Try to add the repository to the db
        if self.add_repo(repo_url):
            # The repository is new, scan from the first commit
            from_timestamp = 0
        else:
            # Get the latest commit recorded on the db
            # `or` clause needed in case the previous scan attempt was broken
            from_timestamp = self.get_repo(repo_url)['last_scan'] or 0

        # Force complete scan
        if force:
            logger.debug('Force complete scan')
            from_timestamp = 0

        # Prepare rules
        rules = self.get_rules(category)
        if exclude:
            rules = list(filter(lambda x: x['id'] not in exclude, rules))
        if not rules:
            raise ValueError('No rules found')

        # Call scanner
        s = scanner(rules)
        logger.debug('Scanning commits...')
        if git_token:
            logger.debug('Authenticate user with token')
            repo_url_scan = repo_url.replace('https://',
                                             f'https://oauth2:{git_token}@')
        else:
            repo_url_scan = repo_url
        latest_timestamp, these_discoveries = s.scan(repo_url_scan,
                                                     since_timestamp=from_timestamp)

        logger.info(f'Detected {len(these_discoveries)} discoveries.')

        # Update latest scan timestamp of the repo
        self.update_repo(repo_url, latest_timestamp)

        # Verify if the SnippetModel is needed, and, in this case, check
        # whether the pre-trained or the generated extractor is wanted
        snippet_with_generator = False
        if 'SnippetModel' in models:
            if generate_snippet_extractor:
                # Here, the scan is being run with the SnippetModel and its
                # generator.
                # Remove the snippet model from the list of models to be run:
                # we will launch it manually at the end, as last model.
                # In fact, the SnippetModel may take some time, and in case we
                # need to generate its extractor this delay will be even higher
                snippet_with_generator = True
                models.remove('SnippetModel')
        else:
            # If the SnippetModel is not chosen, but the generator flag is set
            # to True, do not generate the model (to save time and resources)
            if generate_snippet_extractor:
                logger.debug(
                    'generate_snippet_extractor=True but SnippetModel '
                    'is not in the chosen models. No extractor to generate.')

        # Analyze each new discovery. If it is classified as false positive,
        # update it in the list
        if len(these_discoveries) > 0:
            for model in models:
                # Try to instantiate the model
                try:
                    mm = ModelManager(model)
                except ModuleNotFoundError:
                    logger.warning(f'Model {model} not found. Skip it.')
                    # Continue with another model (if any)
                    continue

                # Analyze discoveries with this model
                analyze_discoveries(mm, these_discoveries, debug)

        # Check if we have to run the snippet model, and, in this case, if it
        # will use the pre-trained extractor or the generated one
        # Yet, since the SnippetModel may be slow, run it only if we still have
        # discoveries to check
        if snippet_with_generator and len(these_discoveries) == 0:
            logger.debug('No more discoveries to filter. Skip SnippetModel.')
        elif snippet_with_generator:
            # Generate extractor and run the model
            logger.info(
                'Generating snippet model (it may take some time...)')
            extractor_folder, extractor_name = \
                self._generate_snippet_extractor(repo_url)
            try:
                # Load SnippetModel with the generated extractor, instead
                # of the default one (i.e., the pre-trained one)
                mm = ModelManager('SnippetModel',
                                  model_extractor=extractor_folder,
                                  binary_extractor=extractor_name)

                analyze_discoveries(mm, these_discoveries, debug)
            except ModuleNotFoundError:
                logger.warning('SnippetModel not found. Skip it.')

        # Insert the discoveries into the db
        discoveries_ids = list()
        if debug:
            for i in tqdm(range(len(these_discoveries))):
                curr_d = these_discoveries[i]
                new_id = self.add_discovery(curr_d['file_name'],
                                            curr_d['commit_id'],
                                            curr_d['line_number'],
                                            curr_d['snippet'],
                                            repo_url,
                                            curr_d['rule_id'],
                                            curr_d['state'])
                if new_id != -1 and curr_d['state'] != 'false_positive':
                    discoveries_ids.append(new_id)
        else:
            # IDs of the discoveries added to the db
            discoveries_ids = self.add_discoveries(these_discoveries, repo_url)
            discoveries_ids = [
                d for i, d in enumerate(discoveries_ids) if d != -1
                and these_discoveries[i]['state'] != 'false_positive']

        return discoveries_ids

    def scan_user(self, username, category=None, models=None, exclude=None,
                  debug=False, generate_snippet_extractor=False, forks=False,
                  git_token=None, api_endpoint='https://api.github.com'):
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
        exclude: list, optional
            A list of rules to exclude
        debug: bool, default `False`
            Flag used to decide whether to visualize the progressbars during
            the scan (e.g., during the insertion of the detections in the db)
        generate_snippet_extractor: bool, default `False`
            Generate the extractor model to be used in the SnippetModel. The
            extractor is generated using the ExtractorGenerator. If `False`,
            use the pre-trained extractor model
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
        if models is None:
            models = []
        if exclude is None:
            exclude = []
        logger.debug(f'Use API endpoint {api_endpoint}')
        if git_token:
            logger.debug('Authenticate user with token')

        g = Github(base_url=api_endpoint,
                   login_or_token=git_token,
                   verify=False)
        missing_ids = {}
        for repo in g.get_user(username).get_repos():
            if not forks and repo.fork:
                # Ignore this repo since it is a fork
                logger.info(f'Ignore {repo} (it is a fork)')
                continue
            # Get repo clone url without .git at the end
            repo_url = repo.clone_url[:-4]
            logger.info(f'Scanning {repo.url}')
            missing_ids[repo_url] = self.scan(repo_url, category=category,
                                              models=models, exclude=exclude,
                                              scanner=GitScanner,
                                              git_token=git_token,
                                              debug=debug)
        return missing_ids

    def scan_wiki(self, repo_url, category=None, scanner=GitScanner,
                  models=None, exclude=None, debug=False, git_token=None):
        """ Scan the wiki of a repository.

        This method simply generates the url of a wiki from the url of its repo,
        and uses the same `scan` method that we use for repositories.

        Parameters
        ----------
        repo_url: str
            The url of the repository
        category: str, optional
            If specified, scan the repo using all the rules of this category,
            otherwise use all the rules in the db
        scanner: class, default: `GitScanner`
            The class of the scanner, a subclass of `scanners.BaseScanner`
        models: list, optional
            A list of models for the ML false positives detection
        exclude: list, optional
            A list of rules to exclude
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
        # The url of a wiki is same as the url of its repo, but ending with
        # `.wiki.git`
        if models is None:
            models = []
        if exclude is None:
            exclude = []
        if git_token:
            logger.debug('Authenticate user with token')
        return self.scan(repo_url + '.wiki.git', category, scanner, models,
                         exclude, debug=debug, git_token=git_token)

    def _generate_snippet_extractor(self, repo_url):
        """ Generate the snippet extractor model adapted to the stylometry of
        the developer of this repository.

        Instantiate a new instance of a ExtractorGenerator, and use it to run
        its method `generate_leak_snippets`.

        Parameters
        ----------
        repo_url: str
            The url of the repository

        Returns
        -------
        str
            The name of the model folder
        str
            The name of the binary for the extractor model
        """
        eg = ExtractorGenerator()
        return eg.generate_leak_snippets(repo_url)
