import tensorflow as tf
from ..base_model import BaseModel


class PathModel(BaseModel):

    def __init__(self,
                 model='melisande1/path_model',
                 tokenizer='distilroberta-base'):
        """ This class classifies a discovery as a false positive according to
        its file path.

        Parameters
        ----------
        model: str, default `path_model`
            The name of the ML model
        binary: str, default `model_path.bin`
            The name of the binary
        """
        super().__init__(model, tokenizer)

    def analyze(self, discoveries):
        """ Analyze a path and predict whether it is a false positive or not.

        Parameters
        ----------

        Returns
        -------
        """
        file_paths = [d['file_name'] for d in discoveries]
        unique_paths = list(set(file_paths))
        encoded_paths = self.tokenizer(unique_paths, truncation=True, padding=True)
        features = {x: encoded_paths[x] for x in self.tokenizer.model_input_names}
        data = tf.data.Dataset.from_tensor_slices((features)).batch(8)
        outputs = self.model.predict(data)
        logits = outputs['logits']
        predictions = tf.argmax(logits, 1)
        path_dict = {}
        for path, pred in zip(unique_paths, predictions):
            path_dict[path] =  pred.numpy()
        n_false_positives = 0
        for d in discoveries:
            if path_dict[d['file_name']] == 1:
                d['state'] = 'false_positive'
                n_false_positives += 1
        return discoveries, n_false_positives
