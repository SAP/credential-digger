import json
import logging
import random
import shutil
from pathlib import Path

import fasttext
import numpy as np
import pkg_resources

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def _create_model_folder(url):
    """ Create the folder for the new model.

    The new folder is created in the `models_data` folder, i.e., at the same
    location of the other models (that can be installed independently from this
    one).
    Structure of the `models_data` folder.
    ```
    models_data
    |- path_model (not mandatory)
    |- snippet_model (independent from this)
    `- snippet_model_author (created with this method)
    ```

    Parameters
    ----------
    url: str
        The url of the repository

    Returns
    -------
    `pathlib.Path`
        The path of the model folder

    Raises
    ------
    FileExistsError
        If the model folder already exists
    """
    # The model name is the name of the author of the repository
    model_name = 'snippet_model_%s' % url.split('/')[-2]
    # Get the models_data folder of credentialdigger
    models_data = Path(pkg_resources.resource_filename('credentialdigger',
                                                       'models_data'))

    # Create model folder. If the model already exists, its folder is already
    # present at this path. In this case, a FileExistsError is raised by the
    # instruction mkdir
    local_model = models_data / model_name
    local_model.mkdir()

    return local_model


def _fill_model_structure(model_folder, model_name, model_version='1.0.0'):
    """ Fill the model folder with subfolders and metafiles.

    Every snippet model has a folder that has to respect the following
    structure (the snippet_model itself is independent from the one we generate
    in this process, and must be installed independently).
    ```
    models_data
    |- ...
    `- snippet_model_author
       |- __init__.py
       |- meta.json
       `- snippet_model_author-1.0.0
          `- extractor.bin
    ```

    Parameters
    ----------
    model_folder: `pathlib.Path`
        The path of the folder of this model
    model_name: str
        The name of the model (i.e., the name of the folder)
    model_version: str, optional
        The version of the model (default `1.0.0`)

    Returns
    -------
    `pathlib.Path`
        The path of the inner folder, where the binaries will be dropped (i.e.,
        the folder identified as `snippet_model_author-version`)
    """
    def create_model_meta(folder, model_name, version):
        metafile = {
            'name': model_name,
            'version': version,
            'credentialdigger_version': '>=1.0.0',
            'parent_package': 'credentialdigger',
            'description': 'SnippetModel extractor from ExtractorGenerator',
            'author': 'credentialdigger-generated',
            'email': 'contact@example.com',
            'url': 'https://example.com',
            'license': 'Apache2'
        }
        jsonfile = model_folder / 'meta.json'
        with open(jsonfile, 'w') as f:
            json.dump(metafile, f)

    # __init__.py
    open(model_folder / '__init__.py', 'w').close()

    # meta.json
    create_model_meta(model_folder, model_name, model_version)

    # Subfolder snippet_model_author-1.0.0
    inner_folder = model_folder / ('%s-%s' % (model_name, model_version))
    inner_folder.mkdir()

    # Return subfolder (it is here that will be dropped the binary model)
    return inner_folder


def _generate_training_dataset(training_data, temp_ds_path):
    """ Pre-process the training data.

    Parameters
    ----------
    training_data: `pandas.DataFrame`
        The training data obtained from the Leak Generator
    temp_ds_path: `pathlib.Path`
        The path of the temp folder containing the dataset

    Returns
    -------
    train_file: str
        The path of the training file
    valid_file: str
        The path of the validation file
    """
    training_data_size = int(round(len(training_data) * 0.99, 2))
    to_write = []
    for idx, row in training_data.iterrows():
        # Find indexes of key and value
        try:
            text = row.text.split()
            idx_key = np.where(np.array(text) == np.array(row.key))[0]
            idx_value = np.where(np.array(text) == np.array(row.value))[0]
            # Consider the first key and the last value
            output = '__label__%s __label__%s %s' % (idx_key[0],
                                                     idx_value[-1],
                                                     row.text)
            to_write.append(output)
        except IndexError:
            # Should never occur since all the patterns have at least one key
            # and at least one value
            logger.error('Text is missing either the key or the value. '
                         'Skip this pattern.\n'
                         'The row in which the error has been detected : ')
            logger.error(row)

    random.shuffle(to_write)

    # Store training files until supervised learning step
    train_file = temp_ds_path / 'extractor.train'
    valid_file = temp_ds_path / 'extractor.valid'
    with open(train_file, 'w') as f:
        for out in to_write[:training_data_size]:
            f.write(out + '\n')
    with open(valid_file, 'w') as f:
        for out in to_write[training_data_size:]:
            f.write(out + '\n')

    # Return path to train and valid extractors
    return str(train_file), str(valid_file)


def _train_model(input_ds, valid_ds, learning_rate=0.1, epoch_model=50,
                 word_ngrams=5, word_vector_dim=100, context_window=5):
    """ Train the model with Fasttext and pre-processed data.

    Only the extractor model of the SnippetModel is trained.

    Parameters
    ----------
    input_ds: str
        The path of the training dataset
    valid_ds: str
        The path of the validation dataset
    learning_rate: float, optional
        The learning rate (default `0.1`)
    epoch_model: int
        The number of epochs (default `50`)
    word_ngrams: int
        The max length of word ngram (default `5`)
    word_vector_dim: int
        The size of word vectors (default `100`)
    context_window: int
        The size of the context window (default `5`)

    Returns
    -------
    `fasttext.FastText._FastText`
        The model object
    """
    model = fasttext.train_supervised(input=input_ds,
                                      lr=learning_rate,
                                      epoch=epoch_model,
                                      wordNgrams=word_ngrams,
                                      dim=word_vector_dim,
                                      ws=context_window,
                                      loss='ova')
    logger.info(f'Evaluation of the model: {model.test(valid_ds)}')
    return model


def create_snippet_model(training_data, repo_url):
    """ Train and save the extractor for the Snippet Model of this repo.

    All the repositories of the same author can use the same extractor. Indeed,
    we assume that the stylometry of an author doesn't change.

    Parameters
    ----------
    training_data: `pandas.DataFrame`
        Pandas DataFrame obtained through the Leak Generator
    repo_url: str
        The url of the repository

    Returns
    -------
    str
        The name of the model folder
    str
        The name of the binary for the extractor model

    Raises
    ------
    FileExistsError
        If the model already exists
    """
    # Create folder for the model
    # It raises a FileExistsError if the folder (thus, the model) already
    # exists
    model_folder = _create_model_folder(repo_url)
    # Fill folder structure
    extractor_folder = _fill_model_structure(model_folder,
                                             model_folder.name)

    # Create a temp folder for storing the temporary datasets
    temp_folder = model_folder / 'temp'
    temp_folder.mkdir()
    # Output the training data and the test data for fasttext
    train, valid = _generate_training_dataset(training_data, temp_folder)

    # Train the model
    model = _train_model(train, valid)

    # Save model
    extractor_bin = extractor_folder / 'model_extractor_adapted.bin'
    model.save_model(str(extractor_bin))

    # Remove temp folder (with its files)
    shutil.rmtree(temp_folder)

    # For being ready to use in the SnippetModel class
    return model_folder.name, extractor_bin.name
