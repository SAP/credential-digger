"""
The 'scan_user' module can be used to scan a GitHub user on the fly from the
terminal. It supports both the Sqlite and Postgres clients.

NOTE: Postgres is used by default. Please make sure that the environment
variables are exported and that the rules have already been added to the
database.

usage: credentialdigger scan_user [-h] [--dotenv DOTENV] [--sqlite SQLITE]
                                  [--category CATEGORY]
                                  [--models MODELS [MODELS ...]] [--debug]
                                  [--git_token GIT_TOKEN]
                                  [--generate_snippet_extractor] [--forks]
                                  [--similarity]
                                  [--api_endpoint API_ENDPOINT]
                                  username

positional arguments:
  username              The username as on github.com

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
  --generate_snippet_extractor
                        Generate the extractor model to be used in the
                        SnippetModel. The extractor is generated using the
                        ExtractorGenerator. If `False`, use the pre-trained
                        extractor model
  --similarity          Build and use the similarity model to compute
                        embeddings and allow for automatic update of similar
                        snippets
  --forks               Scan also repositories forked by this user
  --api_endpoint API_ENDPOINT
                        API endpoint of the git server

"""
import logging

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
        'username', type=str,
        help='The username as on github.com')
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
        '--forks', action='store_true', default=False,
        help='Scan also repositories forked by this user')
    parser.add_argument(
        '--api_endpoint', type=str, default='https://api.github.com',
        help='API endpoint of the git server')
    parser.add_argument(
        '--git_token', default=None, type=str,
        help='Git personal access token to authenticate to the git server')


def run(client, args):
    """
    Scan a GitHub user.

    Parameters
    ----------
    client: `credentialdigger.Client`
        Instance of the client on which to save results
    args: `argparse.Namespace`
        Arguments from command line parser.
    """

    discoveries = client.scan_user(
        username=args.username,
        category=args.category,
        models=args.models,
        debug=args.debug,
        generate_snippet_extractor=args.generate_snippet_extractor,
        similarity=args.similarity,
        forks=args.forks,
        git_token=args.git_token,
        api_endpoint=args.api_endpoint)

    logger.info(f'{len(discoveries)} repositories scanned.')
