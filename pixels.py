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
    for x in range(image.width):
        for y in range(image.height):
            value = image.getpixel((x, y))
            if palette is None and isinstance(value, int):
                value = (value, value, value)
            elif palette is None and isinstance(value, tuple) and len(value) == 4:
                value = value[:3]
            elif palette is not None:
                value = tuple(palette[value * 3: value * 3 + 3])
            if value not in (Color.WHITE.value, Color.OFF_WHITE.value):
                try:
                    yield Pixel(x, y), Color(value)
                except ValueError:
                    raise UnknownColor(value)
