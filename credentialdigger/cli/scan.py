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
import logging
import sys

logger = logging.getLogger(__name__)


def configure_parser(parser):
    """
    Configure arguments for command line parser.

    Parameters
    ----------
    parser: `credentialdigger.cli.customParser`
        Command line parser
    """
    parser.set_defaults(func=run)
    parser.add_argument(
        'repo_url', type=str,
        help='The URL of the git repository to be scanned.')
    parser.add_argument(
        '--category', default=None, type=str,
        help=' If specified, scan the repo using all the rules of this \
            category, otherwise use all the rules in the db')
    parser.add_argument(
        '--models', default=None, nargs='+',
        help='A list of models for the ML false positives detection.\nCannot \
            accept empty lists.')
    parser.add_argument(
        '--exclude', default=None, nargs='+',
        help='A list of rules to exclude')
    parser.add_argument(
        '--force', action='store_true',
        help='Force a complete re-scan of the repository, in case it has \
            already been scanned previously')
    parser.add_argument(
        '--debug', action='store_true',
        help='Flag used to decide whether to visualize the progressbars \
            during the scan (e.g., during the insertion of the detections in \
            the db)')
    parser.add_argument(
        '--generate_snippet_extractor',
        action='store_true',
        help='Generate the extractor model to be used in the SnippetModel. \
            The extractor is generated using the ExtractorGenerator. If \
            `False`, use the pre-trained extractor model')


def run(args, client):
    """
    Scan a git repository.

    Parameters
    ----------
    args: `argparse.Namespace`
        Arguments from command line parser.
    client: `credentialdigger.Client`
        Instance of the client on which to save results

    Returns
    -------
        While this function returns nothing of use to the scanner itself, it
        gives an exit status (integer) that is equal to the number of
        discoveries. If it exits with a value that is equal to 0, then it means
        that the scan detected no leaks in this repo.
    """

    discoveries = client.scan(
        repo_url=args.repo_url,
        category=args.category,
        models=args.models,
        exclude=args.exclude,
        force=args.force,
        debug=args.debug,
        generate_snippet_extractor=args.generate_snippet_extractor)

    sys.exit(len(discoveries))
