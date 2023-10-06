from typing import Optional, NamedTuple

COLOR_THRESHOLD = 250


class Color(NamedTuple):
    red: int
    green: int
    blue: int


WHITE = Color(255, 255, 255)
BLACK = Color(0, 0, 0)
RED = Color(128, 0, 0)
GREY = Color(128, 128, 128)
GREY2 = Color(117, 117, 117)
GREY3 = Color(100, 100, 100)


def get_color_with_threshold(rgb: tuple[int, int, int]) -> Optional["Color"]:
    for color in [WHITE, BLACK, RED, GREY, GREY2, GREY3]:
        if square_distance(color, rgb) < COLOR_THRESHOLD:
            return color


def square_distance(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]):
    r1, g1, b1 = rgb1
    r2, g2, b2 = rgb2
    return (r1 - r2)**2 + (g1 - g2)**2 + (b1 - b2)**2
