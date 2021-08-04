import tensorflow as tf
from ..base_model import BaseModel


class SnippetModel(BaseModel):

    def __init__(self,
                 model='melisande1/pw1',
                 tokenizer='microsoft/codebert-base-mlm',
                 use_auth_token='api_uAUHSJqiZfkfCjBqnoMkUrWGEIsKJcRliN'):
        """ This class classifies discoveries as false positives
        according to snippets.

        Parameters
        ----------
        model: str 
            The transformer model's path
        tokenizer: str
            The tokenizer's path
        use_auth_token: str, optional
            The token to access and download the model from
            the Hugging Face hub
        """
        super().__init__(model, tokenizer, use_auth_token)

    def analyze(self, discoveries):
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
        fp_discoveries = [d for d in discoveries \
                          if d['state'] == 'false_positive']
        new_discoveries = [d for d in discoveries \
                           if d['state'] != 'false_positive']
        snippets = [d['snippet'] for d in new_discoveries]
        data = self.preprocess_data(snippets)
        outputs = self.model.predict(data)
        logits = outputs['logits']
        predictions = tf.argmax(logits, 1)
        n_false_positives = 0
        for d, p in zip(new_discoveries, predictions):
            if p == 0:
                d['state'] = 'false_positive'
                n_false_positives += 1
        discoveries = fp_discoveries + new_discoveries
        return discoveries, n_false_positives

    def preprocess_data(self, snippets):
        """ Compute encodings of snippets and format them to a standard 
        Tensorflow dataset.

        Parameters
        ----------
        snippets: list
            The snippets to be preprocessed

        Returns
        -------
        tf.data.Dataset
            The dataset to be fed to the classifier
        """
        encodings = self.tokenizer(snippets,
                                   truncation=True,
                                   padding=True)
        features = {x: encodings[x] \
                    for x in self.tokenizer.model_input_names}
        dataset = tf.data.Dataset.from_tensor_slices((features)).batch(8)
        return dataset
