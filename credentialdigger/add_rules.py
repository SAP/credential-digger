"""
The 'add_rules' module adds scanning rules from a file to the database.
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


def add_rules(args):
    """
    Add rules to the database

    Parameters
    ----------
    args
        Arguments from command line parser.

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

    if args.sqlite:
        c = SqliteClient(args.sqlite)
        logger.info('Database in use: Sqlite')
    else:
        c = PgClient(dbname=os.getenv('POSTGRES_DB'),
                     dbuser=os.getenv('POSTGRES_USER'),
                     dbpassword=os.getenv('POSTGRES_PASSWORD'),
                     dbhost=os.getenv('DBHOST'),
                     dbport=os.getenv('DBPORT'))
        logger.info('Database in use: Postgres')

    c.add_rules_from_file(args.path_to_rules)

    # This message will not be logged if the above operation fails,
    # hence raising an exception.
    logger.info('The rules have been added successfully.')
