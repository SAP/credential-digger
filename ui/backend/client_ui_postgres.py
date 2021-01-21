from credentialdigger import PgClient
from credentialdigger.client import Discovery

from .client_ui import UiClient


class PgUiClient(UiClient, PgClient):
    def get_discoveries(self, repo_url, file_name=None, where=None, limit=None,
                        offset=None, order_by=None, order_direction='ASC'):
        """ Get all the discoveries of a repository.

        Parameters
        ----------
        repo_url: str
            The url of the repository
        file_name: str, optional
            The filename to filter discoveries on
        TODO: docs

        Returns
        -------
        list
            A list of discoveries (dictionaries)

        Raises
        ------
            TypeError
                If any of the required arguments is missing
        """
        # Build inner query to get paginated unique snippets
        inner_params = [repo_url]
        inner_query = ('SELECT snippet, COUNT(*) OVER() AS total'
                       ' FROM discoveries WHERE repo_url=%s')
        if file_name is not None:
            inner_query += ' AND file_name=%s'
            inner_params.append(file_name)
        if where is not None:
            inner_query += ' AND snippet LIKE %s'
            inner_params.append(f'%{where}%')
        inner_query += ' GROUP BY snippet, state, rule_id'
        if (order_by in ['category', 'snippet', 'state']
                and order_direction in ['asc', 'desc']):
            if order_by == 'category':
                order_by = 'rule_id'
            inner_query += f' ORDER BY {order_by} {order_direction}'
        if limit is not None:
            inner_query += ' LIMIT %s'
            inner_params.append(limit)
        if offset is not None:
            inner_query += ' OFFSET %s'
            inner_params.append(offset)

        # Execute inner query
        snippets = []
        cursor = self.db.cursor()
        cursor.execute(inner_query, tuple(inner_params))
        result = cursor.fetchone()
        total_discoveries = result[1] if result else 0
        while result:
            snippets.append(result[0])
            result = cursor.fetchone()

        # Build outer query to get all occurrences of the paginated snippets
        query = 'SELECT * FROM discoveries WHERE repo_url=%s'
        params = [repo_url]
        if file_name is not None:
            query += ' AND file_name=%s'
            params.append(file_name)
        query += ' AND snippet IN %s'
        params.append(tuple(snippets))

        # Execute outer query
        all_discoveries = []
        cursor.execute(query, tuple(params))
        result = cursor.fetchone()
        while result:
            all_discoveries.append(dict(Discovery(*result)._asdict()))
            result = cursor.fetchone()

        return total_discoveries, all_discoveries

    def get_discoveries_count(self, repo_url=None, file_name=None, where=None):
        """ Get all the discoveries of a repository.

        Parameters
        ----------
        repo_url: str
            The url of the repository
        file_name: str, optional
            The filename to filter discoveries on
        TODO: docs

        Returns
        -------
        list
            A list of discoveries (dictionaries)

        Raises
        ------
            TypeError
                If any of the required arguments is missing
        """
        query = 'SELECT COUNT(*) FROM discoveries'
        params = []
        if repo_url is not None:
            query += ' WHERE repo_url=%s'
            params.append(repo_url)
        if file_name is not None:
            query += ' AND file_name=%s'
            params.append(file_name)
        if where is not None:
            query += ' AND snippet LIKE %%%s%%'
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
                " FROM discoveries WHERE repo_url=%s"
                " GROUP BY file_name"
            ))
