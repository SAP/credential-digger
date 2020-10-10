"""
The 'scan' module can be used to scan a git repository on the fly from the
terminal. It supports both the Sqlite and Postgres clients.

NOTE: Postgres is used by default. Please make sure that the environment
variables are exported and that the rules have already been added to the
database.

This command takes multiple arguments :
  repo_url              <Required> The URL of the git repository to be
                        scanned.
  -h, --help            show this help message and exit
  --category CATEGORY   <Optional> If specified, scan the repo using all the
                        rules of this category, otherwise use all the rules in
                        the db
  --models MODELS [MODELS ...]
                        <Optional> A list of models for the ML false positives
                        detection. Cannot accept empty lists.
  --exclude EXCLUDE [EXCLUDE ...]
                        <Optional> A list of rules to exclude
  --force               <Optional> Force a complete re-scan of the repository,
                        in case it has already been scanned previously
  --debug               <Optional> Flag used to decide whether to visualize
                        the progressbars during the scan (e.g., during the
                        insertion of the detections in the db)
  --generate_snippet_extractor
                        <Optional> Generate the extractor model to be used in
                        the SnippetModel. The extractor is generated using the
                        ExtractorGenerator. If `False`, use the pre-trained
                        extractor model
  --sqlite DB_PATH      <Optional> If specified, use the sqlite client and
                        the db passed as argument (otherwise use postgres)

Usage:
python -m credentialdigger scan REPO_URL --force --debug

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
    'repo_url',
    type=str,
    help='<Required> The URL of the git repository to be scanned.')

parser.add_argument(
    '--category',
    default=None,
    type=str,
    help='<Optional> If specified, scan the repo using all the \
                    rules of this category, otherwise use all the \
                    rules in the db')
"""
This argument is deactivated since the scanner is
expecting a class, not a string.

parser.add_argument('--scanner',
                    default='GitScanner',
                    type=str,
                    help='<Optional> class, default: `GitScanner` \
                        The class of the scanner, a subclass of \
                        `scanners.BaseScanner`'
                    )
"""

parser.add_argument('--models',
                    default=None,
                    nargs='+',
                    help='<Optional> A list of models for the ML \
                                    false positives detection.\n \
                                    Cannot accept empty lists.')

parser.add_argument('--exclude',
                    default=None,
                    nargs='+',
                    help='<Optional> A list of rules to exclude')

parser.add_argument(
    '--force',
    action='store_true',
    help='<Optional> Force a complete re-scan of the repository, \
                    in case it has already been scanned previously')

parser.add_argument(
    '--debug',
    action='store_true',
    help='<Optional> Flag used to decide whether to visualize the \
                    progressbars during the scan (e.g., during the \
                    insertion of the detections in the db)')

parser.add_argument(
    '--generate_snippet_extractor',
    action='store_true',
    help='<Optional> Generate the extractor model to be used in the \
                     SnippetModel. The extractor is generated using the \
                     ExtractorGenerator. If `False`, use the pre-trained \
                     extractor model')

parser.add_argument(
    '--sqlite',
    default=None,
    type=str,
    help='<Optional> If specified, scan the repo using the sqlite client \
                     passing as argument the path of the db.\
                     Otherwise, use postgres (must be up and running)')


def scan(*pip_args):
    """
    Scan a git repository.

    Parameters
    ----------
    *pip_args
        Keyword arguments for pip.

    Returns
    -------
        While this function returns nothing of use to the scanner itself, it
        gives an exit status (integer) that is equal to the number of
        discoveries. If it exits with a value that is equal to 0, then it means
        that the scan detected no leaks in this repo.
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

    discoveries = c.scan(
        repo_url=args.repo_url,
        category=args.category,
        models=args.models,
        exclude=args.exclude,
        force=args.force,
        debug=args.debug,
        generate_snippet_extractor=args.generate_snippet_extractor)

    sys.exit(len(discoveries))
