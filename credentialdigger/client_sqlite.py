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

            CREATE TABLE IF NOT EXISTS embeddings (
                id INTEGER REFERENCES discoveries,
                snippet TEXT,
                embedding TEXT,
                repo_url TEXT REFERENCES repos,
                PRIMARY KEY (id)
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
            snippet, repo_url, rule_id, state) VALUES \
            (?, ?, ?, ?, ?, ?, ?)'
        )

    def add_discoveries(self, discoveries, repo_url):
        """ Bulk add new discoveries.

        Parameters
        ----------
        discoveries: list
            The list of scanned discoveries objects to insert into the database
        repo_url: str
            The repository url of the discoveries

        Returns
        -------
        list
            List of the ids of the inserted discoveries

        Notes
        -----
        This method is not thread-safe: modifying discoveries of the same repo
        while running this method will result in unpredictable discoveries ids
        being returned.
        """
        # Transform argument in list of tuples
        discoveries = [
            (d['file_name'], d['commit_id'], d['line_number'],
             d['snippet'], repo_url, d['rule_id'], d['state'])
            for d in discoveries]

        cursor = self.db.cursor()
        try:
            # Batch insert all discoveries
            cursor.executemany(
                'INSERT INTO discoveries (file_name, commit_id, \
                line_number, snippet, repo_url, rule_id, state) \
                VALUES (?, ?, ?, ?, ?, ?, ?)',
                discoveries
            )
            self.db.commit()

            # Get the ids of inserted discoveries
            discoveries_ids = cursor.execute(
                'SELECT * FROM discoveries WHERE repo_url = ? \
                ORDER BY id DESC LIMIT ?', (repo_url, len(discoveries)))

            return [d[0] for d in discoveries_ids]
        except Error:
            # In case of error in the bulk operation, fall back to adding
            # discoveries RBAR
            self.db.rollback()
            return map(lambda d: self.add_discovery(
                file_name=d['file_name'],
                commit_id=d['commit_id'],
                line_number=d['line_number'],
                snippet=d['snippet'],
                repo_url=repo_url,
                rule_id=d['rule_id'],
                state=d['state']
            ), discoveries)

    def add_embedding(self, discovery_id, repo_url, embedding=None):
        """ Add an embedding to the embeddings table.

        Parameters
        ----------
        discovery_id: int
            The id of the discovery whose embedding is being added
        embedding: list
            The embedding being added
        repo_url: str
            The discovery's repository url
        """
        query = 'INSERT INTO embeddings (id, snippet, embedding, repo_url) \
                VALUES (?, ?, ?, ?);'
        return super().add_embedding(query,
                                     discovery_id,
                                     repo_url,
                                     embedding)

    def add_embeddings(self, repo_url):
        """ Bulk add embeddings.

        Parameters
        ----------
        repo_url: str
            The discoveries' repository url
        """
        query = 'INSERT INTO embeddings (id, snippet, embedding, repo_url) \
                VALUES (?, ?, ?, ?);'
        return super().add_embeddings(query, repo_url)

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

    def delete_discoveries(self, repo_url):
        """ Delete all discoveries of a repository.

        Parameters
        ----------
        repo_url: str
            The repository url of the discoveries to delete

        Returns
        -------
        bool
            `True` if the discoveries were successfully deleted, `False`
            otherwise
        """
        return super().delete_discoveries(
            repo_url=repo_url,
            query='DELETE FROM discoveries WHERE repo_url=?')

    def delete_repo(self, repo_url):
        """ Delete a repository. Also triggers the deletion of
        embeddings for the repository, if present.

        Parameters
        ----------
        repo_url: str
            The url of the repository to delete

        Returns
        -------
        bool
            `True` if the repo was successfully deleted, `False` otherwise
        """
        self.delete_embeddings(repo_url)
        return super().delete_repo(
            repo_url=repo_url,
            query='DELETE FROM repos WHERE url=?')

    def delete_embedding(self, discovery_id):
        """ Delete an embedding.

        Parameters
        ----------
        discovery_id: int
            The id of the discovery whose embedding is being deleted

        Returns
        -------
        bool
            `True` if embedding was successfully deleted,
            `False` otherwise
        """
        return super().delete_embedding(
            query='DELETE FROM embeddings WHERE id=?',
            discovery_id=discovery_id)

    def delete_embeddings(self, repo_url):
        """ Delete all embeddings from a repository.

        Parameters
        ----------
        repo_url: str
            The repository url of the embeddings to delete

        Returns
        -------
        bool
            `True` if embeddings were successfully deleted,
            `False` otherwise
        """
        query = 'DELETE FROM embeddings WHERE repo_url=?;'
        return super().delete_embeddings(query, repo_url)

    def get_repo(self, repo_url):
        """ Get a repository.

        Parameters
        ----------
        repo_url: str
            The url of the repository

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

    def get_embedding(self, discovery_id=None, snippet=None):
        """ Retrieve a discovery embedding.

        This method retrieves the embedding of the discovery whose id is
        passed as argument.
        If no id is provided, the method retrieves the embedding of
        the arguments' snippet.
        If the snippet is missing as well, None is returned.

        Parameters
        ----------
        discovery_id: int
            The id of the discovery whose embedding is being retrieved
        snippet: str
            The snippet whose embedding is being retrieved. Only used if
            discovery_id is not provided

        Returns
        ------
        list
            The embedding
        """

        if discovery_id:
            query = 'SELECT embedding FROM embeddings WHERE id=?'
        elif snippet:
            query = 'SELECT embedding FROM embeddings WHERE snippet=?'
        else:
            return None
        return super().get_embedding(query=query,
                                     discovery_id=discovery_id,
                                     snippet=snippet)

    def get_embeddings(self, repo_url):
        """ Retrieve embeddings for an entire repository.

        Parameters
        ----------
        repo_url: str
            The repository url

        Returns
        -------
        dictionary
            A dictionary with discovery ids as keys and matching
            embeddings as values
        """
        query = 'SELECT id, embedding FROM embeddings WHERE repo_url=?;'
        return super().get_embeddings(query=query, repo_url=repo_url)

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

    def update_discoveries(self, discoveries_ids, new_state):
        """ Change the state of multiple discoveries.

        Parameters
        ----------
        discoveries_ids: list
            The ids of the discoveries to be updated
        new_state: str
            The new state of these discoveries

        Returns
        -------
        bool
            `True` if the update is successful, `False` otherwise
        """
        super().update_discoveries(
            discoveries_ids=discoveries_ids,
            new_state=new_state,
            query='UPDATE discoveries SET state=? WHERE id IN('
                  f'VALUES {", ".join(["?"]*len(discoveries_ids))})')

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
