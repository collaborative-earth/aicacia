from dataclasses import dataclass
from typing import Optional


@dataclass
class Figure:
    title: Optional[str]
    label: Optional[str]
    description: Optional[str]
