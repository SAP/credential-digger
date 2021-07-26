"""
The 'scan' module can be used to scan a git repository on the fly from the
terminal. It supports both the Sqlite and Postgres clients.

NOTE: Postgres is used by default. Please make sure that the environment
variables are exported and that the rules have already been added to the
database.

usage: credentialdigger scan [-h] [--dotenv DOTENV] [--sqlite SQLITE]
                             [--category CATEGORY]
                             [--models MODELS [MODELS ...]] [--debug]
                             [--git_token GIT_TOKEN] [--local] [--force]
                             [--generate_snippet_extractor]
                             [--similarity]
                             repo_url

positional arguments:
  repo_url              The location of a git repository (an url if --local is
                        not set, a local path otherwise)

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
  --local               If True, get the repository from a local directory
                        instead of the web
  --force               Force a complete re-scan of the repository, in case it
                        has already been scanned previously
  --generate_snippet_extractor
                        Generate the extractor model to be used in the
                        SnippetModel. The extractor is generated using the
                        ExtractorGenerator. If `False`, use the pre-trained
                        extractor model
  --similarity          Build and use the similarity model to compute
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
        '--local', action='store_true',
        help='If True, get the repository from a local directory instead of \
            the web')
    parser.add_argument(
        '--force', action='store_true',
        help='Force a complete re-scan of the repository, in case it has \
            already been scanned previously')
    parser.add_argument(
        '--generate_snippet_extractor', action='store_true',
        help='Generate the extractor model to be used in the SnippetModel. \
            The extractor is generated using the ExtractorGenerator. If \
            `False`, use the pre-trained extractor model')
    parser.add_argument(
        '--similarity', action='store_true',
        help='Build and use the similarity model to compute embeddings \
            and allow for automatic update of similar snippets')

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
    discoveries = client.scan(
        repo_url=args.repo_url,
        category=args.category,
        models=args.models,
        force=args.force,
        debug=args.debug,
        generate_snippet_extractor=args.generate_snippet_extractor,
        similarity=args.similarity,
        local_repo=args.local,
        git_token=args.git_token)

    sys.exit(len(discoveries))
