from typing import Collection

from parse_qwantz.box import Box
from parse_qwantz.colors import Color
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage


def get_box(shape: Collection[Pixel], padding=0) -> Box:
    x_min = min(x for x, y in shape)
    x_max = max(x for x, y in shape)
    y_min = min(y for x, y in shape)
    y_max = max(y for x, y in shape)
    return Box(Pixel(x_min - padding, y_min - padding), Pixel(x_max + 1 + padding, y_max + 1 + padding))


def get_shape(pixel: Pixel, image: SimpleImage) -> dict[Pixel, Color]:
    pixels_left = [pixel]
    pixels = {}
    while pixels_left:
        pixel = pixels_left.pop()
        pixels[pixel] = image.get_pixel(pixel)
        for other_pixel in get_neighbor_pixels(pixel):
            if other_pixel not in pixels and other_pixel in image.pixels:
                pixels_left.append(other_pixel)
    return pixels


def get_adjacent_pixels(pixel: Pixel) -> list[Pixel]:
    x, y = pixel
    return [
        Pixel(x - 1, y),
        Pixel(x, y - 1),
        Pixel(x, y + 1),
        Pixel(x + 1, y),
    ]


def get_neighbor_pixels(pixel: Pixel) -> list[Pixel]:
    x, y = pixel
    return [
        Pixel(x - 1, y - 1),
        Pixel(x - 1, y),
        Pixel(x - 1, y + 1),
        Pixel(x, y - 1),
        Pixel(x, y + 1),
        Pixel(x + 1, y - 1),
        Pixel(x + 1, y),
        Pixel(x + 1, y + 1),
    ]
