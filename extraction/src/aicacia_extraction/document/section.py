from dataclasses import dataclass
from typing import Optional


@dataclass
class Section:
    title: Optional[str]
    text: Optional[str]
