import tensorflow as tf
import transformers
from transformers import TFRobertaForSequenceClassification, RobertaTokenizer

from ..base_model import BaseModel

# Silence loggers
tf.get_logger().setLevel('ERROR')
transformers.logging.set_verbosity(transformers.logging.ERROR)


class SnippetModel(BaseModel):

    def __init__(self,
                 model='',
                 tokenizer='microsoft/codebert-base-mlm',
                 use_auth_token=''):
        """
        Parameters
        ----------
        model: str
            the model path
            The transformer model's path
        tokenizer: str
            The tokenizer path
        use_auth_token: str, optional
            The token to access and download the model on the Hugging Face hub
        """
        self.model = TFRobertaForSequenceClassification.from_pretrained(
            model,
            num_labels=2,
            use_auth_token=use_auth_token)
        self.tokenizer = RobertaTokenizer.from_pretrained(tokenizer)

    def analyze_batch(self, discoveries):
        """ Analyze a snippet and predict whether it is a leak or not.
        Change each discovery state in-place.

        Parameters
        ----------
        discoveries: list of dict
            The discoveries to classify

        Returns
        -------
        discoveries: list of dict
            The discoveries, with states updated according to
            the model's predictions
        """
        # We have to classify only the "new" discoveries
        new_discoveries = [d for d in discoveries if d['state'] == 'new']
        no_new_discoveries = [d for d in discoveries if d['state'] != 'new']
        # Create a dataset with all the preprocessed (new) snippets
        data = self._pre_process([d['snippet'] for d in new_discoveries])
        # data = self._preprocess_batch_data(snippets)
        # Compute a prediction for each snippet
        outputs = self.model.predict(data)
        logits = outputs['logits']
        predictions = tf.argmax(logits, 1)
        # Compute the probabilities of the discoveries belonging to each class
        probabilities = tf.nn.softmax(logits).numpy()
        # Compute the hsl hue (color) of a discovery as the square of the
        # probability of it being a FP (in percentage).
        # (The square is chosen to augment contrast.)
        hues = [int((p[0] ** 2) * 100) for p in probabilities]
        # Check predictions and set FP discoveries accordingly
        for d, p, h in zip(new_discoveries, predictions, hues):
            if p == 0:
                d['state'] = 'false_positive'
            d['hue'] = h
        print(hues)
        return new_discoveries + no_new_discoveries

    def analyze(self, discovery):
        """ Analyze a snippet and predict whether it is a leak or not.

        Parameters
        ----------
        discoveries: list of dict
            The discoveries

        Returns
        -------
        discoveries: list of dict
            The discoveries, with states updated according to
            the model's predictions
        n_false_positives: int
            The number of false positives detected by the model
        """
        # Preprocess the snippet
        data = self._pre_process([discovery['snippet']])
        # Classify the processed snippet
        outputs = self.model.predict(data)
        predictions = tf.argmax(outputs['logits'], 1)
        if predictions[0] == 0:
            # The model classified this snippet as a false positive
            # (i.e., spam)
            return True

    def _pre_process(self, snippet):
        """ Compute encodings of snippets and format them to a standard
        Tensorflow dataset.

        Parameters
        ----------
        snippet: list of str
            The snippet to be preprocessed

        Returns
        -------
        tf.data.Dataset
            The dataset to be fed to the classifier
        """
        # In our model, encodings and features are the same
        # So, we don't have to compute features and we can directly use
        # encodings to create the dataset
        encodings = self.tokenizer(snippet,
                                   truncation=True,
                                   padding=True)
        # Transform into a tf dataset
        # Please note that the encodings must be cast to dict in order to avoid
        # a ValueError at the model prediction
        return tf.data.Dataset.from_tensor_slices((dict(encodings))).batch(8)
