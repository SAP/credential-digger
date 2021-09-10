from abc import ABC, abstractmethod


class BaseModel(ABC):

    def __init__(self):
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

    @abstractmethod
    def analyze(self, **kwargs):
        pass

    @abstractmethod
    def analyze_batch(self, **kwargs):
        pass
