from abc import ABC, abstractmethod


class BaseModel(ABC):

    @abstractmethod
    def analyze(self, **kwargs):
        pass

    @abstractmethod
    def analyze_batch(self, **kwargs):
        pass
