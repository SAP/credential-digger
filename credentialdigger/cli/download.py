""" The functions defined in this file have been taken (and adapted) from
Python spaCy module.
Indeed, our goal is to offer, in credentialdigger, the same management of
machine learning models offered in spaCy. This is to say that credentialdigger
will be a standalone module that, when installed by users, offers basic
functions (in our case, it is possible to scan repositories, store data, etc.).

In addition to this, we want to provide several machine learning models
independent from credentialdigger, that can be downloaded and installed a
posteriori in order to provide additional features.

In our use case these models are used to filter out false positive discoveries.

usage: credentialdigger download [-h] [--dotenv DOTENV]
                                 model [pip_args [pip_args ...]]

positional arguments:
  model            The name of the model. It must be an environment variable.
  pip_args         Keyword arguments for pip.

optional arguments:
  -h, --help       show this help message and exit
  --dotenv DOTENV  The path to the .env file which will be used in all
                   commands. If not specified, the one in the current
                   directory will be used (if present).

"""

import importlib
import logging
import os
import subprocess
import sys
from pathlib import Path

_data_path = Path(importlib.import_module(
    'credentialdigger').__file__).parent / 'models_data'

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


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
        'model', type=str,
        help='The name of the model. It must be an environment variable.')
    parser.add_argument(
        'pip_args', nargs='*', default=None, help='Keyword arguments for pip.')


# ############################################################################
# Methods adapted from
# https://github.com/explosion/spaCy/blob/master/spacy/cli/download.py


def run(args):
    """ Download a model and link it to the credental digger models_data
    folder.

    Parameters
    ----------
    model: str
        The name of the model. It must be an environment variable.
    pip_args: list
        Keyword arguments for pip.
    """
    model = args.model
    dl = download_model(model, args.pip_args)
    if dl != 0:  # if download subprocess doesn't return 0, exit
        sys.exit(dl)
    logger.info('Download successful')

    # Create symlink because the model is installed via a shortcut like
    # 'path_model' (i.e., the name of the environment variable).
    # Get the name of the model (e.g., path_model) considering that the
    # download address is similar to https://IP:PORT/path_model-1.0.0.tar.gz
    model_fullname = os.getenv(model).split('/')[-1].split('-')[0]
    model_shortcut = model  # Maybe it's just the name of the tar
    try:
        # Get package path here because link uses
        # pip.get_installed_distributions() to check if model is a
        # package, which fails if model was just installed via
        # subprocess
        package_path = get_package_path(model_fullname)
        link(model_fullname,
             model_shortcut,
             force=True,
             model_path=package_path)
    except:  # noqa: E722
        # Dirty, but since spacy.download and the auto-linking is
        # mostly a convenience wrapper, it's best to show a success
        # message and loading instructions, even if linking fails.
        logger.error(
            'Download successful but linking failed\n'
            f'Creating a shortcut link for {model} did not work '
            '(maybe you do not have admin permissions?)'
        )
    # If a model is downloaded and then loaded within the same process, our
    # is_package check currently fails, because pkg_resources.working_set
    # is not refreshed automatically (from spaCy #3923).
    require_package(model_fullname)


def download_model(modelname, user_pip_args=None):
    """ Download a file.
    Parameters
    ----------
    model: str
        The name of the model. It must be an environment variable.
    user_pip_args: list, optional
        Arguments for pip.

    Returns
    -------
    int
        The `subprocess.call` return code, i.e., `1` if the download of the
        model was successful.
    """
    download_url = os.getenv(modelname)
    if not download_url:
        logger.critical('Error: model missing. Abort operation.')
        return -1
    pip_args = ['--no-cache-dir']
    if user_pip_args:
        pip_args.extend(user_pip_args)
    cmd = [sys.executable, '-m', 'pip', 'install'] + pip_args + [download_url]
    return subprocess.call(cmd, env=os.environ.copy())


def require_package(name):
    """ Set a required package in the actual working set.

    Parameters
    ----------
    name: str
        The name of the package.

    Returns
    -------
    bool:
        True if the package exists, False otherwise.
    """
    try:
        import pkg_resources

        pkg_resources.working_set.require(name)
        return True
    except:  # noqa: E722
        return False


# ############################################################################
# Methods adapted from
# https://github.com/explosion/spaCy/blob/master/spacy/cli/link.py


def link(origin, link_name, force=True, model_path=None):
    """ Create a symlink for models within the `credentialdigger/models_data`
    directory.

    This method accepts either the name of a pip package, or the
    local path to the model data directory.
    Linking models allows loading them with the client (e.g., during a scan),
    or by the `ModelManager`.

    Parameters
    ----------
    origin: str
        Package name or local path to model.
    link_name: str
        Name of the shortcut link to create.
    force: bool
        Force overwriting of existing link (default `True`).
    model_path: str, optional
        Path of the `credentialdigger` package to be used.

    Example
    -------
    >>> link(origin="path_model_full_name",
             link_name="path_model",
             force=True,
             model_path="/home/user/venv/.../credentialdigger")
    # Creates a link from origin to /home/.../credentialdigger/models_data

    Raises
    ------
    Exception
        If it is not possible to create the symlink.
    """
    if is_package(origin):
        model_path = get_package_path(origin)
    else:
        model_path = Path(origin) if model_path is None else Path(model_path)
    if not model_path.exists():
        logger.error('Could not locate model data.\n'
                     f'The data should be located in {str(model_path)}')

    data_path = get_data_path()

    if not data_path or not data_path.exists():
        creddig_loc = Path(__file__).parent.parent
        logger.error(
            'Can not find the credentialdigger models data path'
            ' to create model symlink.\n'
            'Make sure a directory `/models_data` exists within your '
            'credentialdigger installation and try again.\n'
            f'The data directory should be located here: {str(creddig_loc)}'
        )

    link_path = get_data_path() / link_name

    if link_path.is_symlink() and not force:
        logger.warning(
            f'Link {link_name} already exists\n'
            'To overwrite an existing link, use the --force flag'
        )
    elif link_path.is_symlink():  # does a symlink exist?
        # NB: It's important to check for is_symlink here and not for exists,
        # because invalid/outdated symlinks would return False otherwise.
        link_path.unlink()
    elif link_path.exists():  # does it exist otherwise?
        # NB: Check this last because valid symlinks also "exist".
        logger.warning(
            f'Can not overwrite symlink {link_name}\n'
            'This can happen if your data directory contains a directory '
            'or file of the same name.'
        )

    details = "%s --> %s" % (str(model_path), str(link_path))
    try:
        # Create a symlink. Used for model shortcut links.
        link_path.symlink_to(model_path)
    except:  # noqa: E722
        # This is quite dirty, but just making sure other errors are caught.
        logger.error(
            f'Could not link model to {link_name}'
            'Creating a symlink in `credentialdigger/models_data` failed. '
            'Make sure you have the required permissions and try re-running '
            'the command as admin, or use a virtualenv. '
            'You can still create the symlink manually.',
        )
        logger.error(details)
        raise
    logger.info(f'Linking successful.\nDetails : {details}')
    logger.info('You can now use the model from credentialdigger.')


# ############################################################################
# Methods adapted from
# https://github.com/explosion/spaCy/blob/master/spacy/util.py


def get_package_path(name):
    """ Get the path to an installed package.

    Parameters
    ----------
    name: str
        The package name.

    Returns
    -------
    `pathlib.Path`
        The path to the installed package.
    """
    name = name.lower()  # use lowercase version to be safe
    # Here we're importing the module just to find it. This is worryingly
    # indirect, but it's otherwise very difficult to find the package.
    pkg = importlib.import_module(name)
    return Path(pkg.__file__).parent


def is_package(name):
    """ Check if string maps to a package installed via pip.

    Parameters
    ----------
    name: str
        The name of a package.

    Returns
    -------
    bool
        True if the package is installed, False otherwise.
    """
    import pkg_resources

    name = name.lower()  # compare package name against lowercase name
    packages = pkg_resources.working_set.by_key.keys()
    for package in packages:
        if package.lower().replace("-", "_") == name:
            return True
    return False


def get_data_path(require_exists=True):
    """ Get path to credentialdigger models_data directory.

    Parameters
    ----------
    require_exists: bool
        Only return path if it exists, otherwise None.

    Returns
    -------
    `pathlib.Path`
        Data path (or None).
    """
    if not require_exists:
        return _data_path
    else:
        return _data_path if _data_path.exists() else None
