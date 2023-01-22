from typing import Collection

from box import Box
from colors import Color
from pixels import Pixel
from simple_image import SimpleImage


def get_box(shape: Collection[Pixel]) -> Box:
    x_min = min(x for x, y in shape)
    x_max = max(x for x, y in shape)
    y_min = min(y for x, y in shape)
    y_max = max(y for x, y in shape)
    return Box(Pixel(x_min, y_min), Pixel(x_max, y_max))


def get_shape(pixel: Pixel, image: SimpleImage) -> dict[Pixel, Color]:
    pixels_left = [pixel]
    pixels = {}
    while pixels_left:
        pixel = pixels_left.pop()
        pixels[pixel] = image.get_pixel(pixel)
        for other_pixel in get_adjacent_pixels(pixel):
            if other_pixel not in pixels and other_pixel in image.pixels:
                pixels_left.append(other_pixel)
    return pixels


def get_adjacent_pixels(pixel: Pixel):
    x, y = pixel
    return [
        (x - 1, y - 1),
        (x - 1, y),
        (x - 1, y + 1),
        (x, y - 1),
        (x, y + 1),
        (x + 1, y - 1),
        (x + 1, y),
        (x + 1, y + 1),
    ]
