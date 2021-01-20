from credentialdigger import Client, PgClient
from psycopg2 import Error, connect

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
        query = 'SELECT * FROM discoveries WHERE repo_url=%s'
        params = [repo_url]
        if file_name is not None:
            query += ' AND file_name=%s'
            params.append(file_name)
        if where is not None:
            query += ' AND snippet LIKE %%%s%%'
            params.append(where)
        if limit is not None:
            query += ' LIMIT %s'
            params.append(limit)
        if offset is not None:
            query += ' OFFSET %s'
            params.append(offset)
        if order_by is not None:
            query += 'ORDER BY %s %s'
            params.append(order_by, order_direction)

        return super().get_discoveries(query, params)
