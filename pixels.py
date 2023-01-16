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

    def find_color(self, box: tuple[Pixel, Pixel]) -> Color:
        (x0, y0), (x1, y1) = box
        for x in range(x0, x1):
            for y in range(y0, y1):
                if (x, y) in self.pixels:
                    return self.pixels[(x, y)]
        return Color.WHITE

    def is_on_edge(self, pixel: Pixel) -> bool:
        x, y = pixel
        return x in (0, self.width - 1) or y in (0, self.height - 1)


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
