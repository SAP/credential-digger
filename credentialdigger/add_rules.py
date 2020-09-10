"""
The 'add_rules' modules add scanning rules from a file to the database.
This module supports both Sqlite & Postegres databases.

This command takes multiple arguments:
path_to_rules       <Required> The path of the file that contains the rules.

--sqlite DB_PATH    <Optional> If specified, use the sqlite client and
                        the db passed as argument (otherwise use postgres)

Usage:
python -m credentialdigger add_rules /path/rules.yml

"""
import argparse
import logging
import os
import sys

from credentialdigger import PgClient, SqliteClient

logger = logging.getLogger(__name__)


class customParser(argparse.ArgumentParser):
    def error(self, message):
        logger.error(f'{message}')
        self.print_help()
        exit()


parser = customParser()

parser.add_argument(
    'path_to_rules',
    type=str,
    help='<Required> The path of the file that contains the rules.')

parser.add_argument(
    '--sqlite',
    default=None,
    type=str,
    help='<Optional> If specified, scan the repo using the sqlite client \
                     passing as argument the path of the db.\
                     Otherwise, use postgres (must be up and running)')

def add_rules(*pip_args):
    """
    Add rules to the database

    Parameters
    ----------
    *pip_args
        Keyword arguments for pip.

    Raises
    ------
        FileNotFoundError
            If the file does not exist
        ParserError
            If the file is malformed
        KeyError
            If one of the required attributes in the file (i.e., rules, regex,
            and category) is missing
    """

    args = parser.parse_args(pip_args)

    if args.sqlite:
        c = SqliteClient(args.sqlite)
        logger.info('Database in use: Sqlite')
    else:
        c = PgClient(dbname=os.getenv('POSTGRES_DB'),
                     dbuser=os.getenv('POSTGRES_USER'),
                     dbpassword=os.getenv('POSTGRES_PASSWORD'),
                     dbhost=os.getenv('DBHOST'),
                     dbport=int(os.getenv('DBPORT')))
        logger.info('Database in use: Postgres')

    c.add_rules_from_file(args.path_to_rules)

    # This message will not be logged if the above operation fails,
    # hence raising an exception.
    logger.info('The rules have been added successfully.')