from abc import ABC, abstractmethod
from typing import Optional
from .section import Section

class Document(ABC):
    @abstractmethod
    def abstract(self) -> Optional[str]:
        pass

    @classmethod
    @abstractmethod
    def from_path(cls, path: str):
        pass

    @abstractmethod
    def references(self) -> Optional[str]:
        pass

    @abstractmethod
    def sections(self) -> list[Section]:
        pass

    @abstractmethod
    def title(self) -> Optional[str]:
        pass
