from dataclasses import dataclass
from typing import Optional


@dataclass
class Section:
    title: Optional[str]
    text: Optional[str]

    def __str__(self) -> str:
        return f"{self.title}\n{self.text}"
