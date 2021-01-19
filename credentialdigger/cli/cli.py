import argparse
import logging
import os
import sys

from dotenv import load_dotenv

from credentialdigger import PgClient, SqliteClient

logger = logging.getLogger(__name__)


class customParser(argparse.ArgumentParser):
    def error(self, message):
        logger.error(f'{message}\n')
        self.print_help()
        exit()


def main():
    from . import add_rules, download, scan, scan_user, scan_wiki

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

    parser_scan_base = customParser(add_help=False)
    parser_scan_base.add_argument(
        '--category', default=None, type=str,
        help='If specified, scan the repo using all the rules of this \
            category, otherwise use all the rules in the db')
    parser_scan_base.add_argument(
        '--models', default=None, nargs='+',
        help='A list of models for the ML false positives detection.\nCannot \
            accept empty lists.')
    parser_scan_base.add_argument(
        '--exclude', default=None, nargs='+',
        help='A list of rules to exclude')
    parser_scan_base.add_argument(
        '--debug', action='store_true',
        help='Flag used to decide whether to visualize the progressbars \
            during the scan (e.g., during the insertion of the detections in \
            the db)')
    parser_scan_base.add_argument(
        '--git_token', default=None, type=str,
        help='Git personal access token to authenticate to the git server')

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
        parents=[parser_dotenv, parser_sqlite, parser_scan_base])
    scan.configure_parser(parser_scan)

    # scan_user subparser configuration
    parser_scan_user = subparsers.add_parser(
        'scan_user', help='Scan a GitHub user',
        parents=[parser_dotenv, parser_sqlite, parser_scan_base])
    scan_user.configure_parser(parser_scan_user)

    # scan_user subparser configuration
    parser_scan_wiki = subparsers.add_parser(
        'scan_wiki', help='Scan the wiki of a repository',
        parents=[parser_dotenv, parser_sqlite, parser_scan_base])
    scan_wiki.configure_parser(parser_scan_wiki)

    # Run the parser
    if len(sys.argv) == 1:
        main_parser.print_help()
        exit()

    args = main_parser.parse_args(sys.argv[1:])
    # If specified, load dotenv from the given path. Otherwise load from cwd
    load_dotenv(dotenv_path=args.dotenv, verbose=True)

    if args.func in [scan.run, add_rules.run, scan_user.run, scan_wiki.run]:
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
        args.func(client, args)
    else:
        args.func(args)
