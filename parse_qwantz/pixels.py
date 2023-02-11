from functools import cache
from logging import getLogger
from typing import Iterable, NamedTuple

from PIL import Image

from parse_qwantz.colors import Color

logger = getLogger()


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
    unknown_colors = False
    for i, value in enumerate(values):
        x = i % width
        y = i // width
        value = normalize_color(value, palette)
        if value != white:
            try:
                color = Color(value)
            except ValueError:
                color = Color.get_with_threshold(value)
                if not color:
                    if not unknown_colors:
                        unknown_colors = True
                        logger.warning(f"Unknown color at {(x, y)}: {value}. Replacing with black.")
                    color = Color.BLACK
            if color != Color.WHITE:
                yield Pixel(x, y), color


@cache
def normalize_color(
    color: int | tuple[int, int, int] | tuple[int, int, int, int], palette: tuple[int, ...] | None
) -> tuple[int, int, int]:
    if palette is None and isinstance(color, int):
        color = (color, color, color)
    elif palette is None and isinstance(color, tuple) and len(color) == 4:
        color = color[:3]
    elif palette is not None:
        color = palette[color * 3: color * 3 + 3]
    return color
