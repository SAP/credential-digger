from abc import ABC, abstractmethod
from pathlib import Path

import fasttext
import pkg_resources
import srsly

fasttext.FastText.eprint = lambda x: None


class BaseModel(ABC):

    def __init__(self, model):
        self.model = fasttext.load_model(model)

    @abstractmethod
    def analyze(self, **kwargs):
        pass

    def get_model_meta(self, model_path):
        """ Get model's meta.json from the directory path of the model, and
        validate its contents. This method is ported from spaCy.
        `https://github.com/explosion/spaCy/blob/master/spacy/util.py#L231`

        Parameters
        ----------
        model_path: `pathlib.Path`
            Path to model directory.

        Returns
        -------
        dict
            The model's meta data.

        Raises
        ------
        FileNotFoundError
            If the model is not found (i.e., it has not been downloaded) or if
            the model misses the metafile.
        ValueError
            If the metafile of the model `meta.json` is malformed.
        """
        if not model_path.exists():
            raise FileNotFoundError(
                'Module not found at path %s. Verify it is installed.' %
                str(model_path))

        meta_path = model_path / 'meta.json'
        if not meta_path.is_file():
            raise FileNotFoundError(
                'It seems that model %s is  missing meta.json file.'
                'Contact maintainers' % model_path.name)

        meta = srsly.read_json(meta_path)
        for setting in ['name', 'version']:
            if setting not in meta or not meta[setting]:
                raise ValueError(
                    'Malformed meta.json file, value %s is missing. '
                    'Contact maintainers' % setting)
        return meta

    def find_model_file(self, model_name, binary_name):
        """ Find the path of the binary file of a model.

        Parameters
        ----------
        model_name: str
            The name of the model (e.g., `path_model`).
        binary_name: str
            The name of the binary file of the model (e.g., `vocabulary.bin`).

        Returns
        -------
        str
            The path to access the file `binary_name`.

        Raises
        ------
        ModuleNotFoundError
            If model `model_name` is not found (i.e., it has not been
            installed, or installation was broken).
        """
        # Get the models_data folder of credentialdigger
        # All the models should be linked here after the download
        models_data = Path(pkg_resources.resource_filename('credentialdigger',
                                                           'models_data'))

        # Verify the model was downloaded
        if model_name not in set([d.name for d in models_data.iterdir()]):
            raise ModuleNotFoundError('Model %s not found. Verify its '
                                      'installation.' % model_name)

        # Look for the binary file
        model_path = models_data / model_name
        model_meta = self.get_model_meta(model_path)
        model_version = '%s-%s' % (model_meta['name'], model_meta['version'])

        return str(models_data / model_name / model_version / binary_name)
