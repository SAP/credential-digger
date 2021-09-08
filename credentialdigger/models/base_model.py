from abc import ABC, abstractmethod

from transformers import TFRobertaForSequenceClassification, RobertaTokenizer


class BaseModel(ABC):

    def __init__(self, model, tokenizer, use_auth_token=None):
        """
        Parameters
        ----------
        model: str
            the model path
        tokenizer: str
            The tokenizer path
        use_auth_token: str, optional
            The token to access the model on the Hugging Face hub
        """
        if globals().get('snippet_model'):
            self.model = globals()['snippet_model']
        else:
            self.model = TFRobertaForSequenceClassification.from_pretrained(
                model,
                num_labels=2,
                use_auth_token=use_auth_token)
            global snippet_model
            snippet_model = self.model
        if globals().get('snippet_tokenizer'):
            self.tokenizer = globals()['snippet_tokenizer']
        else:
            self.tokenizer = RobertaTokenizer.from_pretrained(tokenizer)
            global snippet_tokenizer
            snippet_tokenizer = self.tokenizer

    @abstractmethod
    def analyze(self, **kwargs):
        pass
