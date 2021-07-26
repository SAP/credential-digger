"""
The 'scan_wiki' module can be used to scan the wiki of a git repository on the
fly from the terminal. It supports both the Sqlite and Postgres clients.

NOTE: Postgres is used by default. Please make sure that the environment
variables are exported and that the rules have already been added to the
database.

usage: credentialdigger scan_wiki [-h] [--dotenv DOTENV] [--sqlite SQLITE]
                                  [--category CATEGORY]
                                  [--models MODELS [MODELS ...]]
                                  [--debug]
                                  [--git_token GIT_TOKEN]
                                  repo_url

positional arguments:
  repo_url              The url of the repository

optional arguments:
  -h, --help            show this help message and exit
  --dotenv DOTENV       The path to the .env file which will be used in all
                        commands. If not specified, the one in the current
                        directory will be used (if present).
  --sqlite SQLITE       If specified, scan the repo using the sqlite client
                        passing as argument the path of the db. Otherwise, use
                        postgres (must be up and running)
  --category CATEGORY   If specified, scan the repo using all the rules of
                        this category, otherwise use all the rules in the db
  --models MODELS [MODELS ...]
                        A list of models for the ML false positives detection.
                        Cannot accept empty lists.
  --debug               Flag used to decide whether to visualize the
                        progressbars during the scan (e.g., during the
                        insertion of the detections in the db)
  --git_token GIT_TOKEN
                        Git personal access token to authenticate to the git
                        server

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
        help='The url of the repository')
    parser.add_argument(
        '--git_token', default=None, type=str,
        help='Git personal access token to authenticate to the git server')


def run(client, args):
    """
    Scan a git repository.

    Parameters
    ----------
    client: `credentialdigger.Client`
        Instance of the client on which to save results
    args: `argparse.Namespace`
        Arguments from command line parser.

    Returns
    -------
        While this function returns nothing of use to the scanner itself, it
        gives an exit status (integer) that is equal to the number of
        discoveries. If it exits with a value that is equal to 0, then it means
        that the scan detected no leaks in this repo.
    """

    discoveries = client.scan_wiki(
        repo_url=args.repo_url,
        category=args.category,
        models=args.models,
        debug=args.debug,
        git_token=args.git_token)

    sys.exit(len(discoveries))
