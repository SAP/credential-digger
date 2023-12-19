"""
The 'scan' module can be used to scan a git repository on the fly from the
terminal. It supports both the Sqlite and Postgres clients.

NOTE: Postgres is used by default. Please make sure that the environment
variables are exported and that the rules have already been added to the
database.


usage: credentialdigger scan_pr [-h] [--dotenv DOTENV] [--sqlite SQLITE]
                                [--pr PULL_REQUEST_NUMBER]
                                [--api_endpoint API_ENDPOINT]
                                [--category CATEGORY]
                                [--models MODELS [MODELS ...]]
                                [--force] [--debug]
                                [--git_token GIT_TOKEN]
                                [--similarity]
                                repo_url

positional arguments:
  repo_url              The location of a git repository
  pr                    The number of the pull request to scan

optional arguments:
  -h, --help            show this help message and exit
  --dotenv DOTENV       The path to the .env file which will be used in all
                        commands. If not specified, the one in the current
                        directory will be used (if present).
  --sqlite SQLITE       If specified, scan the repo using the sqlite client
                        passing as argument the path of the db. Otherwise, use
                        postgres (must be up and running)
  --api_endpoint API_ENDPOINT
                        API endpoint of the git server (default is the public
                        github, i.e., `https://api.github.com`)
  --category CATEGORY   If specified, scan the PR using all the rules of
                        this category, otherwise use all the rules in the db
  --models MODELS [MODELS ...]
                        A list of models for the ML false positives detection.
                        Cannot accept empty lists.
  --force               Wipe previous scan results, in case this repository
                        has already been scanned previously
  --debug               Flag used to decide whether to visualize the
                        progressbars during the scan (e.g., during the
                        insertion of the detections in the db)
  --git_token GIT_TOKEN
                        Git personal access token to authenticate to the git
                        server
 --similarity           Build and use the similarity model to compute
                        embeddings and allow for automatic update of similar
                        snippets

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
        help='The location of a git repository (an url if --local is not set, \
            a local path otherwise)')
    parser.add_argument(
        '--pr', type=int, required=True,
        help='The number of pull request to scan')
    parser.add_argument(
        '--api_endpoint', type=str, default='https://api.github.com',
        help='API endpoint of the git server')
    parser.add_argument(
        '--force', action='store_true',
        help='Force a complete re-scan of the repository, in case it has \
            already been scanned previously')
    parser.add_argument(
        '--similarity', action='store_true',
        help='Build and use the similarity model to compute embeddings \
            and allow for automatic update of similar snippets')
    parser.add_argument(
        '--git_token', default=None, type=str,
        help='Git personal access token to authenticate to the git server')


def run(client, args):
    """
    Scan a pull request in a git repository.

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
    logger.info(f'Scan pull request number {args.pr}')
    discoveries = client.scan_pull_request(
        repo_url=args.repo_url,
        pr_number=args.pr,
        category=args.category,
        models=args.models,
        force=args.force,
        debug=args.debug,
        similarity=args.similarity,
        git_token=args.git_token,
        api_endpoint=args.api_endpoint)

    sys.exit(len(discoveries))
