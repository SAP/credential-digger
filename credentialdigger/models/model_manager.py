from . import *


class ModelManager:

    def __init__(self, model, **kwargs):
        """ Create an instance of a model.

        Notes
        -----
        The class name of the model must be in the global namespace (i.e.,
        imported in the `__init__.py` file of the `models` folder)

        Parameters
        ----------
        model: str
            The class name of a model

        Raises
        ------
        ModuleNotFoundError
            if `model` is not in `globals()`
        """
        # If the class models has been imported in the __init__.py, it is
        # in the global namespace
        this_model = globals().get(model, None)

        if not this_model:
            # Raise an exception
            raise ModuleNotFoundError('Model %s not found.' % model)

        # Instantiate the model
        self.model = this_model(**kwargs)

    def launch_model(self, discovery):
        """ Classify a discovery using the model loaded by this instance of the
        class.

        Parameters
        ----------
        discovery: dict
            A discovery dictionary

        Returns
        -------
        bool
            True if the model classifies this discovery as a false positive
        """
        return self.model.analyze(discovery)
