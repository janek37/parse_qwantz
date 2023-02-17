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

    def find_pixel(self, pixels: list[Pixel]) -> Pixel | None:
        for pixel in pixels:
            if pixel in self.pixels:
                return pixel

    def is_on_edge(self, pixel: Pixel) -> bool:
        x, y = pixel
        return x in (0, self.width - 1) or y in (0, self.height - 1)

    def distance_to_edge(self, pixel: Pixel) -> int:
        return min(pixel.x, pixel.y, self.width - pixel.x - 1, self.height - pixel.y - 1)
