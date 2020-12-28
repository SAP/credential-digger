import os
import sys
import logging
import argparse

from dotenv import load_dotenv

from credentialdigger import PgClient, SqliteClient

logger = logging.getLogger(__name__)


class customParser(argparse.ArgumentParser):
    def error(self, message):
        logger.error(f'{message}\n')
        self.print_help()
        exit()


def main():
    from . import scan, add_rules, download

    # Main parser configuration
    main_parser = customParser('credentialdigger')
    subparsers = main_parser.add_subparsers()

    # Common parsers configuration
    parser_dotenv = customParser(add_help=False)
    parser_dotenv.add_argument(
        '--dotenv', type=str, default=None,
        help='The path to the .env file which will be used in all \
            commands. If not specified, the one in the current directory will \
            be used (if present).')
    parser_sqlite = customParser(add_help=False)
    parser_sqlite.add_argument(
        '--sqlite', type=str, default=None,
        help='If specified, scan the repo using the sqlite client \
            passing as argument the path of the db. Otherwise, use postgres \
            (must be up and running)')

    # download subparser configuration
    parser_download = subparsers.add_parser(
        'download', parents=[parser_dotenv],
        help='Download and link a machine learning model')
    download.configure_parser(parser_download)

    # add_rules subparser configuration
    parser_add_rules = subparsers.add_parser(
        'add_rules', help='Add scanning rules from a file to the database',
        parents=[parser_dotenv, parser_sqlite])
    add_rules.configure_parser(parser_add_rules)

    # scan subparser configuration
    parser_scan = subparsers.add_parser(
        'scan', help='Scan a git repository',
        parents=[parser_dotenv, parser_sqlite])
    scan.configure_parser(parser_scan)

    # Run the parser
    if len(sys.argv) == 1:
        main_parser.print_help()
        exit()

    args = main_parser.parse_args(sys.argv[1:])
    # If specified, load dotenv from the given path. Otherwise load from cwd
    load_dotenv(dotenv_path=args.dotenv, verbose=True)

    if args.func in [scan.run, add_rules.run]:
        # Connect to db only when running commands that need it
        if args.sqlite:
            client = SqliteClient(args.sqlite)
            logger.info('Database in use: Sqlite')
        else:
            client = PgClient(dbname=os.getenv('POSTGRES_DB'),
                              dbuser=os.getenv('POSTGRES_USER'),
                              dbpassword=os.getenv('POSTGRES_PASSWORD'),
                              dbhost=os.getenv('DBHOST'),
                              dbport=os.getenv('DBPORT'))
            logger.info('Database in use: Postgres')
        args.func(args, client)
    else:
        args.func(args)
