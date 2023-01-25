from functools import cache
from typing import Iterable, NamedTuple

from PIL import Image

from colors import Color


class Pixel(NamedTuple):
    x: int
    y: int


class UnknownColor(ValueError):
    pass


def get_pixels(image: Image) -> Iterable[tuple[Pixel, Color]]:
    palette = image.getpalette()
    palette = tuple(palette) if palette else None
    values = image.getdata()
    width = image.width
    white = Color.WHITE.value
    off_white = Color.OFF_WHITE.value
    for i, value in enumerate(values):
        x = i % width
        y = i // width
        value = normalize_color(value, palette)
        if value != white and value != off_white:
            try:
                yield Pixel(x, y), Color(value)
            except ValueError:
                raise UnknownColor(value)


@cache
def normalize_color(
    color: int | tuple[int, int, int] | tuple[int, int, int, int], palette: tuple[int, ...]
) -> tuple[int, int, int]:
    if palette is None and isinstance(color, int):
        color = (color, color, color)
    elif palette is None and isinstance(color, tuple) and len(color) == 4:
        color = color[:3]
    elif palette is not None:
        color = palette[color * 3: color * 3 + 3]
    return color
