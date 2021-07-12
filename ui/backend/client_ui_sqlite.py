from credentialdigger import SqliteClient
from credentialdigger.client import Discovery

from .client_ui import UiClient


class SqliteUiClient(UiClient, SqliteClient):
    def get_discoveries(self, repo_url, file_name=None, state_filter=None,
                        where=None, limit=None, offset=None, order_by=None,
                        order_direction='ASC'):
        """ Get all the discoveries of a repository.
        Supports full pagination by passing the respective parameters.

        Parameters
        ----------
        repo_url: str
            The url of the repository
        file_name: str, optional
            The name of the file to filter discoveries on
        state_filter: str, optional
            State on which to filter discoveries on
        where: str, optional
            Part of text contained in the snippet to filter discoveries on
            (using SQL LIKE clause)
        limit: int, optional
            Number of unique discoveries to return. All occurrences of the
            unique discoveries will be returned. (A unique discovery
            corresponds to a distinct (snippet, state, rule_id) value)
        offset: int, optional
            Number of unique discoveries to start pagination from
        order_by: str, optional
            Name of the property on which to order results
            (properties currently supported: category, snippet, state)
        order_direction: str, optional
            Direction of the sorting (either 'asc' or 'desc')

        Returns
        -------
        int
            The total number of discoveries (non-paginated)
        list
            A list of discoveries (dictionaries)
        """
        # Build inner query to get paginated unique snippets
        inner_params = [repo_url]
        inner_query = ('SELECT snippet, state, COUNT(*) OVER() AS total'
                       ' FROM discoveries WHERE repo_url=?')
        if file_name is not None:
            inner_query += ' AND file_name=?'
            inner_params.append(file_name)
        if state_filter is not None:
            inner_query += ' AND state=?'
            inner_params.append(state_filter)
        if where is not None:
            inner_query += ' AND snippet LIKE ?'
            inner_params.append(f'%{where}%')
        inner_query += ' GROUP BY snippet, state, rule_id'
        if (order_by in ['category', 'snippet', 'state']
                and order_direction in ['asc', 'desc']):
            if order_by == 'category':
                order_by = 'rule_id'
            inner_query += f' ORDER BY {order_by} {order_direction}'
            if order_by != 'snippet':
                inner_query += ', snippet ASC'
        if limit is not None:
            inner_query += ' LIMIT ?'
            inner_params.append(limit)
        if offset is not None:
            inner_query += ' OFFSET ?'
            inner_params.append(offset)

        # Execute inner query
        snippets = []
        n_snippets = 0
        cursor = self.db.cursor()
        cursor.execute(inner_query, tuple(inner_params))
        result = cursor.fetchone()
        total_discoveries = result[2] if result else 0
        while result:
            n_snippets += 1
            snippets.extend([result[0], result[1]])
            result = cursor.fetchone()

        if len(snippets) == 0:
            return 0, []

        # Build outer query to get all occurrences of the paginated snippets
        query = 'SELECT * FROM discoveries WHERE repo_url=?'
        params = [repo_url]
        if file_name is not None:
            query += ' AND file_name=?'
            params.append(file_name)
        if state_filter is not None:
            query += ' AND state=?'
            params.append(state_filter)
        query += (f' AND(snippet, state) IN('
                  f'VALUES {", ".join(["(?, ?)"]*n_snippets)})')
        params.extend(snippets)

        # Execute outer query
        all_discoveries = []
        cursor.execute(query, tuple(params))
        result = cursor.fetchone()
        while result:
            all_discoveries.append(dict(Discovery(*result)._asdict()))
            result = cursor.fetchone()

        return total_discoveries, all_discoveries

    def get_discoveries_count(self, repo_url=None, file_name=None, where=None):
        """ Get the total number of discoveries.

        Parameters
        ----------
        repo_url: str, optional
            The url of the repository. (returns the total number of discoveries
            in the database if not provided)
        file_name: str, optional
            The name of the file to filter discoveries on
        where: str, optional
            Part of text contained in the snippet to filter discoveries on
            (using SQL LIKE clause)

        Returns
        -------
        int
            The total number of discoveries
        """
        query = 'SELECT COUNT(*) FROM discoveries'
        params = []
        if repo_url is not None:
            query += ' WHERE repo_url=?'
            params.append(repo_url)
        if file_name is not None:
            query += ' AND file_name=?'
            params.append(file_name)
        if where is not None:
            query += ' AND snippet LIKE %%?%%'
            params.append(where)

        return super().get_discoveries_count(query, params)

    def get_files_summary(self, repo_url):
        """ Get aggregated discoveries info on all files of a repository.

        Parameters
        ----------
        repo_url: str
            The url of the repository

        Returns
        -------
        list
            A list of files with aggregated data (dictionaries)
        """
        return super().get_files_summary(
            repo_url=repo_url,
            query=(
                "SELECT file_name,"
                " COUNT(*) AS tot_discoveries,"
                " COUNT(CASE WHEN state='new' THEN 1 END) AS new,"
                " COUNT(CASE WHEN state='false_positive' THEN 1 END) AS false_positives,"
                " COUNT(CASE WHEN state='addressing' THEN 1 END) AS addressing,"
                " COUNT(CASE WHEN state='not_relevant' THEN 1 END) AS not_relevant"
                " FROM discoveries WHERE repo_url=?"
                " GROUP BY file_name"
            ))
