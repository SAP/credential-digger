from psycopg2 import connect, Error

from .client import Client


class PgClient(Client):
    def __init__(self, dbname, dbuser, dbpassword,
                 dbhost='localhost', dbport=5432):
        """ Create a connection to the postgres database.

        The PgClient is the interface object in charge of all the operations on
        the database, and in charge of launching the scans.

        Parameters
        ----------
        dbname: str
            The name of the database
        dbuser: str
            The user of the database
        dbpassword: str
            The password for the user
        dbhost: str, default `localhost`
            The host of the database
        dbport: int, default `5432`
            The port for the database connection

        Raises
        ------
        OperationalError
            If the Client cannot connect to the database
        """
        super().__init__(connect(
            host=dbhost,
            dbname=dbname,
            user=dbuser,
            password=dbpassword,
            port=dbport),
            Error)

    def query_check(self, query, *args):
        cursor = self.db.cursor()
        try:
            cursor.execute(query, args)
            self.db.commit()
            return bool(cursor.fetchone()[0])
        except (TypeError, IndexError):
            """ A TypeError is raised if any of the required arguments is
            missing. """
            self.db.rollback()
            return False
        except self.Error:
            self.db.rollback()

    def query_id(self, query, *args):
        cursor = self.db.cursor()
        try:
            cursor.execute(query, args)
            self.db.commit()
            return int(cursor.fetchone()[0])
        except (TypeError, IndexError):
            """ A TypeError is raised if any of the required arguments is
            missing. """
            self.db.rollback()
            return -1
        except Error:
            self.db.rollback()
            return -1

    def add_discovery(self, file_name, commit_id, snippet, repo_url, rule_id,
                      state='new'):
        """ Add a new discovery.

        Parameters
        ----------
        file_name: str
            The name of the file that produced the discovery
        commit_id: str
            The id of the commit introducing the discovery
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
        return super().add_discovery(
            file_name=file_name,
            commit_id=commit_id,
            snippet=snippet,
            repo_url=repo_url,
            rule_id=rule_id,
            state=state,
            query='INSERT INTO discoveries (file_name, commit_id, snippet, \
            repo_url, rule_id, state) VALUES (%s, %s, %s, %s, %s, %s) \
            RETURNING id')

    def add_repo(self, repo_url):
        """ Add a new repository.

        Do not set the latest commit (it will be set when the repository is
        scanned).

        Parameters
        ----------
        repo_url: str
            The url of the repository

        Returns
        -------
        bool
            `True` if the insert was successfull, `False` otherwise
        """
        return super().add_repo(
            repo_url=repo_url,
            query='INSERT INTO repos (url) VALUES (%s) RETURNING true')

    def add_rule(self, regex, category, description=''):
        """ Add a new rule.

        Parameters
        ----------
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
        return super().add_rule(
            regex=regex,
            category=category,
            description=description,
            query='INSERT INTO rules (regex, category, description) \
                    VALUES (%s, %s, %s) RETURNING id')

    def delete_rule(self, ruleid):
        """Delete a rule from database

        Parameters
        ----------
        ruleid: int
            The id of the rule that will be deleted.

        Returns
        ------
        False
            If the removal operation fails
        True
            Otherwise
        """
        return super().delete_rule(
            ruleid=ruleid,
            query='DELETE FROM rules WHERE id=%s')

    def delete_repo(self, repo_url):
        """ Delete a repository.

        Parameters
        ----------
        repo_id: int
            The id of the repo to delete

        Returns
        -------
        bool
            `True` if the repo was successfully deleted, `False` otherwise
        """
        return super().delete_repo(
            repo_url=repo_url,
            query='DELETE FROM repos WHERE url=%s RETURNING true')

    def get_repo(self, repo_url):
        """ Get a repository.

        Parameters
        ----------
        repo_url: str
            The url of the repo

        Returns
        -------
        dict
            A repository (an empty dictionary if the url does not exist)
        """
        return super().get_repo(
            repo_url=repo_url,
            query='SELECT * FROM repos WHERE url=%s')

    def get_rules(self, category=None):
        """ Get the rules.

        Differently from other get methods, here we pass the category as
        argument. This is due to the fact that categories may have a slash
        (e.g., `auth/password`). Encoding such categories in the url would
        cause an error on the server side.

        Parameters
        ----------
        category: str, optional
            If specified get all the rules, otherwise get all the rules of this
            category

        Returns
        -------
        list
            A list of rules (dictionaries)
        """
        return super().get_rules(
            category=category,
            category_query='SELECT * FROM rules WHERE category=%s')

    def get_rule(self, rule_id):
        """ Get a rule.

        Parameters
        ----------
        rule_id: int
            The id of the rule

        Returns
        -------
        dict
            A rule
        """
        return super().get_rule(
            rule_id=rule_id,
            query='SELECT * FROM rules WHERE id=%s')

    def get_discoveries(self, repo_url):
        """ Get all the discoveries of a repository.

        Parameters
        ----------
        repo_url: str
            The url of the repository

        Returns
        -------
        list
            A list of discoveries (dictionaries)
        """
        return super().get_discoveries(
            repo_url=repo_url,
            query='SELECT * FROM discoveries WHERE repo_url=%s')

    def get_discovery(self, discovery_id):
        """ Get a discovery.

        Parameters
        ----------
        discovery_id: int
            The id of the discovery

        Returns
        -------
        dict
            A discovery
        """
        return super().get_discovery(
            discovery_id=discovery_id,
            query='SELECT * FROM discoveries WHERE id=%s')

    def get_discovery_group(self, repo_url, state=None):
        """ Get all the discoveries of a repository, grouped by file_name,
        snippet, and state.

        Parameters
        ----------
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
        """
        return super().get_discovery_group(
            repo_url=repo_url,
            state_query='SELECT file_name, snippet, count(id), state FROM \
            discoveries WHERE repo_url=%s AND state=%s GROUP BY file_name,\
            snippet, state',
            query='SELECT file_name, snippet, count(id), state FROM \
            discoveries WHERE repo_url=%s GROUP BY file_name, snippet, state')

    def update_repo(self, url, last_commit):
        """ Update the last commit of a repo.

        After a scan, record what is the most recent commit scanned, such that
        another (future) scan will not process the same commits twice.

        Parameters
        ----------
        url: str
            The url of the repository scanned
        last_commit: str
            The most recent commit scanned

        Returns
        -------
        bool
            `True` if the update is successful, `False` otherwise
        """
        super().update_repo(
            url=url,
            last_commit=last_commit,
            query='UPDATE repos SET last_commit=%s WHERE url=%s RETURNING true'
        )

    def update_discovery(self, discovery_id, new_state):
        """ Change the state of a discovery.

        Parameters
        ----------
        discovery_id: int
            The id of the discovery to be updated
        new_state: str
            The new state of this discovery

        Returns
        -------
        bool
            `True` if the update is successful, `False` otherwise
        """
        super().update_discovery(
            discovery_id=discovery_id,
            new_state=new_state,
            query='UPDATE discoveries SET state=%s WHERE id=%s RETURNING true')

    def update_discovery_group(self, repo_url, file_name, snippet, new_state):
        """ Change the state of a group of discoveries.

        A group of discoveries is identified by the url of their repository,
        their filename,and their snippet.

        Parameters
        ----------
        repo_url: str
            The url of the repository
        file_name: str
            The name of the file
        snippet: str
            The snippet
        new_state: str
            The new state of this discovery

        Returns
        -------
        bool
            `True` if the update is successful, `False` otherwise
        """
        super().update_discovery_group(
            repo_url=repo_url,
            file_name=file_name,
            snippet=snippet,
            new_state=new_state,
            query='UPDATE discoveries SET state=%s WHERE repo_url=%s \
            and file_name=%s and snippet=%s RETURNING true')
