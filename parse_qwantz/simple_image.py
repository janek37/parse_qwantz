from dataclasses import dataclass

from PIL import Image

from parse_qwantz.box import Box
from parse_qwantz.colors import Color
from parse_qwantz.pixels import Pixel, get_pixels


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

    def find_color(self, box: Box) -> Color:
        (x0, y0), (x1, y1) = box
        for x in range(x0, x1):
            for y in range(y0, y1):
                if Pixel(x, y) in self.pixels:
                    return self.pixels[Pixel(x, y)]
        return Color.WHITE

    def find_pixel(self, box: Box) -> Pixel | None:
        (x0, y0), (x1, y1) = box
        for x in range(x0, x1):
            for y in range(y0, y1):
                if Pixel(x, y) in self.pixels:
                    return Pixel(x, y)

    def is_on_edge(self, pixel: Pixel) -> bool:
        x, y = pixel
        return x in (0, self.width - 1) or y in (0, self.height - 1)
