from credentialdigger import SqliteClient

from .client_ui import UiClient


class SqliteUiClient(UiClient, SqliteClient):
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
        query = 'SELECT * FROM discoveries WHERE repo_url=?'
        params = [repo_url]
        if file_name is not None:
            query += ' AND file_name=?'
            params.append(file_name)
        if where is not None:
            query += ' AND snippet LIKE %%?%%'
            params.append(where)
        if limit is not None:
            query += ' LIMIT ?'
            params.append(limit)
        if offset is not None:
            query += ' OFFSET ?'
            params.append(offset)
        if order_by is not None:
            query += 'ORDER BY ? ?'
            params.append(order_by, order_direction)

        return super().get_discoveries(query, params)

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
