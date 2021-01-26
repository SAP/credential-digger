from sqlite3 import Error, connect

from .client import Client


class SqliteClient(Client):
    def __init__(self, path):
        """ Create/connects to a sqlite database.

        The SqliteClient is the interface object in charge of all the
        operations on the database, and in charge of launching the scans.

        Parameters
        ----------
        path: str
            Database file (':memory:' is in RAM memory)
        """
        super().__init__(connect(database=path, check_same_thread=False),
                         Error)
        # Create database if not exist
        cursor = self.db.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS repos(
                url TEXT NOT NULL UNIQUE,
                last_scan INTEGER,
                PRIMARY KEY (url)
            );

            CREATE TABLE IF NOT EXISTS rules(
                id INTEGER,
                regex TEXT NOT NULL UNIQUE,
                category TEXT,
                description TEXT,
                PRIMARY KEY (id)
            );

            CREATE TABLE IF NOT EXISTS discoveries(
                id INTEGER,
                file_name TEXT NOT NULL,
                commit_id TEXT NOT NULL,
                line_number INTEGER DEFAULT -1,
                snippet TEXT DEFAULT '',
                repo_url TEXT,
                rule_id INTEGER,
                state TEXT NOT NULL DEFAULT 'new',
                timestamp TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M','now', 'localtime')),
                PRIMARY KEY (id),
                FOREIGN KEY (repo_url) REFERENCES repos ON DELETE CASCADE ON UPDATE CASCADE,
                FOREIGN KEY (rule_id) REFERENCES rules ON DELETE SET NULL ON UPDATE CASCADE
            );

            PRAGMA foreign_keys=ON;
        """)
        cursor.close()
        self.db.commit()

    def query_check(self, query, *args):
        cursor = self.db.cursor()
        try:
            cursor.execute(query, args)
            self.db.commit()
            return cursor.rowcount < 1
        except (TypeError, IndexError):
            """ A TypeError is raised if any of the required arguments is
            missing. """
            self.db.rollback()
            return False
        except self.Error:
            self.db.rollback()
        cursor.close()

    def query_id(self, query, *args):
        cursor = self.db.cursor()
        try:
            cursor.execute(query, args)
            self.db.commit()
            return cursor.lastrowid
        except (TypeError, IndexError):
            """ A TypeError is raised if any of the required arguments is
            missing. """
            self.db.rollback()
            return -1
        except Error:
            self.db.rollback()
            return -1
        cursor.close()

    def add_discovery(self, file_name, commit_id, line_number, snippet,
                      repo_url, rule_id, state='new'):
        """ Add a new discovery.

        Parameters
        ----------
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
        return super().add_discovery(
            file_name=file_name,
            commit_id=commit_id,
            line_number=line_number,
            snippet=snippet,
            repo_url=repo_url,
            rule_id=rule_id,
            state=state,
            query='INSERT INTO discoveries (file_name, commit_id, line_number, \
            snippet, repo_url, rule_id, state) VALUES (?, ?, ?, ?, ?, ?, ?)'
        )

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
        return super().add_repo(repo_url=repo_url,
                                query='INSERT INTO repos (url) VALUES (?);')

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
            query='INSERT INTO rules (regex, category, description) VALUES (?, ?, ?)'
        )

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
        return super().delete_rule(ruleid=ruleid,
                                   query='DELETE FROM rules WHERE id=?')

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
            query='DELETE FROM repos WHERE url=?'
        )

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
        return super().get_repo(repo_url=repo_url, query='SELECT * FROM repos WHERE url=?')

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
            category_query='SELECT * FROM rules WHERE category=?')

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
        return super().get_rule(rule_id=rule_id,
                                query='SELECT * FROM rules WHERE id=?')

    def get_discoveries(self, repo_url, file_name=None):
        """ Get all the discoveries of a repository.

        Parameters
        ----------
        repo_url: str
            The url of the repository
        file_name: str, optional
            The filename to filter discoveries on

        Returns
        -------
        list
            A list of discoveries (dictionaries)
        """
        query = 'SELECT * FROM discoveries WHERE repo_url=?'
        if file_name:
            query += ' AND file_name=?'
        return super().get_discoveries(
            repo_url=repo_url,
            file_name=file_name,
            query=query)

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
            query='SELECT * FROM discoveries WHERE id=?')

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
        return super().get_discovery_group(repo_url=repo_url,
                                           state_query='SELECT file_name, snippet, count(id), state FROM \
                discoveries WHERE repo_url=? AND state=? GROUP BY file_name,\
                snippet, state',
                                           query='SELECT file_name, snippet, count(id), state FROM discoveries \
                WHERE repo_url=? GROUP BY file_name, snippet, state'
                                           )

    def update_repo(self, url, last_scan):
        """ Update the last scan timestamp of a repo.

        After a scan, record the timestamp of the last scan, such that
        another (future) scan will not process the same commits twice.

        Parameters
        ----------
        url: str
            The url of the repository scanned
        last_scan: int
            The timestamp of the last scan

        Returns
        -------
        bool
            `True` if the update is successful, `False` otherwise
        """
        super().update_repo(
            url=url, last_scan=last_scan,
            query='UPDATE repos SET last_scan=? WHERE url=?'
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
            new_state=new_state, discovery_id=discovery_id,
            query='UPDATE discoveries SET state=? WHERE id=?'
        )

    def update_discovery_group(self, new_state, repo_url, file_name, snippet=None):
        """ Change the state of a group of discoveries.

        A group of discoveries is identified by the url of their repository,
        their filename,and their snippet.

        Parameters
        ----------
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
        query = 'UPDATE discoveries SET state=? WHERE repo_url=?'
        if file_name is not None:
            query += ' and file_name=?'
        if snippet is not None:
            query += ' and snippet=?'
        super().update_discovery_group(
            new_state=new_state, repo_url=repo_url, file_name=file_name,
            snippet=snippet, query=query)
