"""
The 'scan_user' module can be used to scan a GitHub user on the fly from the
terminal. It supports both the Sqlite and Postgres clients.

NOTE: Postgres is used by default. Please make sure that the environment
variables are exported and that the rules have already been added to the
database.

This command takes multiple arguments :
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
    --exclude EXCLUDE [EXCLUDE ...]
                          A list of rules to exclude
    --debug               Flag used to decide whether to visualize the
                          progressbars during the scan (e.g., during the
                          insertion of the detections in the db)
    --generate_snippet_extractor
                          Generate the extractor model to be used in the
                          SnippetModel. The extractor is generated using the
                          ExtractorGenerator. If `False`, use the pre-trained
                          extractor model
    --forks               Scan also repositories forked by this user
    --git_token GIT_TOKEN
                          Git personal access token to authenticate to the git
                          server
    --api_endpoint API_ENDPOINT
                          API endpoint of the git server


Usage:
python -m credentialdigger scan_user USERNAME --debug

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
        '--debug', action='store_true',
        help='Flag used to decide whether to visualize the progressbars \
            during the scan (e.g., during the insertion of the detections in \
            the db)')
    parser.add_argument(
        '--generate_snippet_extractor', action='store_true',
        help='Generate the extractor model to be used in the SnippetModel. \
            The extractor is generated using the ExtractorGenerator. If \
            `False`, use the pre-trained extractor model')
    parser.add_argument(
        '--forks', action='store_true', default=False,
        help='Scan also repositories forked by this user')
    parser.add_argument(
        '--git_token', type=str, default=None,
        help='Git personal access token to authenticate to the git server')
    parser.add_argument(
        '--api_endpoint', type=str, default='https://api.github.com',
        help='API endpoint of the git server')


def run(args, client):
    """
    Scan a GitHub user.

    Parameters
    ----------
    args: `argparse.Namespace`
        Arguments from command line parser.
    client: `credentialdigger.Client`
        Instance of the client on which to save results
    """

    discoveries = client.scan_user(
        username=args.username,
        category=args.category,
        models=args.models,
        exclude=args.exclude,
        debug=args.debug,
        generate_snippet_extractor=args.generate_snippet_extractor,
        forks=args.forks,
        git_token=args.git_token,
        api_endpoint=args.api_endpoint)

    logger.info("{} repositories scanned.".format(len(discoveries)))
