from dataclasses import dataclass
from enum import Enum


@dataclass
class Bounds:
    top: int
    left: int
    bottom: int
    right: int

    def width(self) -> int:
        return self.right - self.left

    def center_x(self) -> int:
        return (self.right + self.left) // 2


@dataclass
class Element:
    page_num: int
    index: int
    bounds: Bounds
    type_name: str
    text: str


class LayoutType(str, Enum):
    DEFAULT = 'DEFAULT'
    TWO_COLUMNS_LEFT = 'LEFT'
    TWO_COLUMNS_RIGHT = 'RIGHT'
    INVERTED_T_LEFT_UP = 'LEFT_UP'
    INVERTED_T_RIGHT_UP = 'RIGHT_UP'
    INVERTED_T_LOW = 'LOW'
    T_LEFT_LOW = 'LEFT_LOW'
    T_RIGHT_LOW = 'RIGHT_LOW'
    T_UP = 'UP'


@dataclass
class PostprocessPageZoneResult:
    layout_type: LayoutType
    paragraphs: list[str]
    last_text_fragment: str | None


@dataclass
class PostprocessPageResult:
    page_number: int
    zones: list[PostprocessPageZoneResult]


@dataclass
class PostprocessResult:
    pages: list[PostprocessPageResult]
    references: list[str]
