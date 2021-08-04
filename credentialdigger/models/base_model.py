from abc import ABC, abstractmethod

from transformers import TFRobertaForSequenceClassification, RobertaTokenizer


class BaseModel(ABC):

    def __init__(self, model, tokenizer):
        self.model = TFRobertaForSequenceClassification.from_pretrained(
            model,
            num_labels=2,
            use_auth_token='api_uAUHSJqiZfkfCjBqnoMkUrWGEIsKJcRliN')
        self.tokenizer = RobertaTokenizer.from_pretrained(tokenizer)

    @abstractmethod
    def analyze(self, **kwargs):
        pass
