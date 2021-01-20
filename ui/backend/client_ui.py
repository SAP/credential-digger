from credentialdigger import Client
from credentialdigger.client import Discovery


class UiClient(Client):
    def get_discoveries(self, query, params):
        """ Get all the discoveries of a repository.

        Parameters
        ----------
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
        all_discoveries = []
        cursor = self.db.cursor()
        cursor.execute(query, tuple(params))
        result = cursor.fetchone()
        while result:
            all_discoveries.append(dict(Discovery(*result)._asdict()))
            result = cursor.fetchone()
        return all_discoveries
