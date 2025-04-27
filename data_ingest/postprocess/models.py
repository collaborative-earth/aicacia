from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Bounds:
    top: int
    left: int
    bottom: int
    right: int

    def width(self) -> int:
        return self.right - self.left

    def middle_x(self) -> int:
        return (self.right + self.left) // 2


@dataclass
class Element:
    page_num: int
    index: int
    bounds: Bounds
    type_name: str
    text: str
    ocr_text: str | None = None

    def __eq__(self, other):
        if isinstance(other, Element):
            return self.index == other.index
        return False


class ClusterCategory(Enum):
    DEFAULT = 1
    TABLE = 2
    FIGURE = 3
    CONTOUR_GROUP = 4


@dataclass
class ElementCluster:
    header: Element
    other_elements: list[Element] = field(default_factory=list)
    category: ClusterCategory = ClusterCategory.DEFAULT

    def all_elements(self):
        return [self.header] + self.other_elements

    def __len__(self):
        return 1 + len(self.other_elements)

    def __getitem__(self, index):
        if isinstance(index, int):
            if index == 0:
                return self.header
            elif index > 0:
                return self.other_elements[index - 1]
            else:
                index += (1 + len(self.other_elements))
                return self.__getitem__(index)
        else:
            raise TypeError("Invalid index type")

    def __iter__(self):
        return iter([self.header] + self.other_elements)

    def __contains__(self, item):
        if not isinstance(item, Element):
            return False

        return self.header == item or (item in self.other_elements)


class LayoutType(Enum):
    DEFAULT = 1
    TWO_COLUMNS_LEFT = 2
    TWO_COLUMNS_RIGHT = 3
    INVERTED_T_LEFT_UP = 4
    INVERTED_T_RIGHT_UP = 5
    INVERTED_T_LOW = 6
    T_LEFT_LOW = 7
    T_RIGHT_LOW = 8
    T_UP = 9
