from enum import Enum
from typing import Optional

COLOR_THRESHOLD = 250


class Color(Enum):
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (128, 0, 0)

    @classmethod
    def get_with_threshold(cls, rgb: tuple[int, int, int]) -> Optional["Color"]:
        for color in cls:
            if square_distance(color.value, rgb) < COLOR_THRESHOLD:
                return color


def square_distance(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]):
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    return (r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2
