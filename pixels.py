from dataclasses import dataclass
from typing import Iterable

from PIL import Image

from colors import Color

Pixel = tuple[int, int]


class UnknownColor(ValueError):
    pass


@dataclass
class SimpleImage:
    width: int
    height: int
    pixels: dict[Pixel, Color]

    @classmethod
    def from_image(cls, image: Image):
        return cls(image.width, image.height, dict(get_pixels(image)))

    def get_pixel(self, pixel: Pixel) -> Color:
        # caution: no bounds checking!
        return self.pixels.get(pixel, Color.WHITE)


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
            if value != Color.WHITE.value:
                try:
                    yield (x, y), Color(value)
                except ValueError:
                    raise UnknownColor(value)
