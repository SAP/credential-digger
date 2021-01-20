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
        query += (' AND snippet IN (SELECT snippet FROM ('
                  'SELECT DISTINCT snippet, state, rule_id FROM discoveries WHERE repo_url=%s')
        params.append(repo_url)
        if file_name is not None:
            query += ' AND file_name=%s'
            params.append(file_name)
        if where is not None:
            query += ' AND snippet LIKE %%%s%%'
            params.append(where)
        if order_by in ['category', 'snippet', 'state']:
            if order_by == 'category':
                order_by = 'rule_id'
                # FIX: refactor this
            query += f' ORDER BY {order_by}'
            # params.append(order_direction)
            # TODO: order by ENUM does not accept ASC|DESC but needs an integer
        if limit is not None:
            query += ' LIMIT %s'
            params.append(limit)
        if offset is not None:
            query += ' OFFSET %s'
            params.append(offset)

        query += ') as temp)'

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
                " FROM discoveries WHERE repo_url=%s"
                " GROUP BY file_name"
            ))

    # def get_files_summary(self, repo_url, where=None, limit=None, offset=None,
    #                       order_by=None, order_direction='ASC'):
    #     """ Get aggregated discoveries info on all files of a repository.

    #     Parameters
    #     ----------
    #     repo_url: str
    #         The url of the repository

    #     Returns
    #     -------
    #     list
    #         A list of files with aggregated data (dictionaries)
    #     """
    #     query = (
    #         "SELECT file_name,"
    #         " COUNT(*) AS tot_discoveries,"
    #         " COUNT(CASE WHEN state='new' THEN 1 END) AS new,"
    #         " COUNT(CASE WHEN state='false_positive' THEN 1 END) AS false_positives,"
    #         " COUNT(CASE WHEN state='addressing' THEN 1 END) AS addressing,"
    #         " COUNT(CASE WHEN state='not_relevant' THEN 1 END) AS not_relevant"
    #         " FROM discoveries WHERE repo_url=%s"
    #     )

    #     params = [repo_url]

    #     if where is not None:
    #         query += ' AND file_name LIKE %%%s%%'
    #         params.append(where)
    #     if limit is not None:
    #         query += ' LIMIT %s'
    #         params.append(limit)
    #     if offset is not None:
    #         query += ' OFFSET %s'
    #         params.append(offset)
    #     if order_by is not None:
    #         query += 'ORDER BY %s %s'
    #         params.append(order_by, order_direction)

    #     query += " GROUP BY file_name"
    #     return super().get_files_summary(
    #         repo_url=repo_url,
    #         query=query)
