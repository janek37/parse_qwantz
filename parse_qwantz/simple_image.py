from dataclasses import dataclass

from PIL import Image

from parse_qwantz.colors import Color, WHITE
from parse_qwantz.pixels import Pixel, get_pixels


@dataclass
class SimpleImage:
    width: int
    height: int
    pixels: dict[Pixel, Color]

    @classmethod
    def from_image(cls, image: Image, trim_top: bool = False):
        if trim_top:
            pixels = {pixel: color for pixel, color in get_pixels(image) if pixel.x > 240 or pixel.y > 46}
        else:
            pixels = dict(get_pixels(image))
        return cls(image.width, image.height, pixels)

    def get_pixel(self, pixel: Pixel) -> Color:
        # caution: no bounds checking!
        return self.pixels.get(pixel, WHITE)

    def is_on_edge(self, pixel: Pixel) -> bool:
        x, y = pixel
        return x in (0, self.width - 1) or y in (0, self.height - 1)

    def distance_to_edge(self, pixel: Pixel) -> int:
        return min(pixel.x, pixel.y, self.width - pixel.x - 1, self.height - pixel.y - 1)
