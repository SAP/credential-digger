from sqlite3 import Error, connect

from .client import Client
from .snippet_similarity import (build_embedding_model, compute_similarity,
                                 compute_snippet_embedding)

import re
import traceback

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
                embedding TEXT,
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

    def update_similar_snippets(self,
                                target_snippet,
                                state,
                                repo_url,
                                file_name=None,
                                threshold=0.96):
        discoveries = self.get_discoveries(repo_url, file_name)
        model = build_embedding_model()
        """ Compute target snippet embedding """
        target_snippet_embedding = compute_snippet_embedding(target_snippet,
                                                             model)
        n_updated_snippets = 0
        for d in discoveries:
            if d['state'] == 'new':
                """ Compute similarity of target snippet and snippet """
                embedd = "".join(d['embedding'])
                embedd = embedd.strip(',')
                str_embedding = re.split(",",embedd)
                str_embedding = "".join(str_embedding).strip("[").strip("]")
                str_embedding = re.split(" ",str_embedding)
                embedding = [float(emb) for emb in str_embedding]
                similarity = compute_similarity(target_snippet_embedding, embedding)
                if similarity > threshold:
                    n_updated_snippets += 1
                    self.update_discovery(d['id'], state)
        return n_updated_snippets
