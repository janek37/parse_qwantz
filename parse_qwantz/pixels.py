from functools import cache
from logging import getLogger
from typing import Iterable, NamedTuple

from PIL import Image

from parse_qwantz.colors import Color, square_distance, get_color_with_threshold, WHITE

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
    unknown_colors = False
    for i, value in enumerate(values):
        x = i % width
        y = i // width
        value = normalize_color(value, palette)
        if value != WHITE:
            color = get_color_with_threshold(value)
            if not color:
                if not unknown_colors:
                    unknown_colors = True
                    logger.warning(f"Unknown color at {(x, y)}: {value}.")
                color = Color(*value)
            if color != WHITE:
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


def remove_subsequence(sorted_pixels: list[Pixel], subsequence: list[Pixel]) -> list[Pixel]:
    sub_iter = iter(subsequence)
    next_pixel = next(sub_iter)
    pixels = []
    for pixel in sorted_pixels:
        while next_pixel is not None and pixel > next_pixel:
            try:
                next_pixel = next(sub_iter)
            except StopIteration:
                next_pixel = None
        if pixel != next_pixel:
            pixels.append(pixel)
    return pixels


def is_ask_professor_science(image: Image) -> bool:
    palette = image.getpalette()
    palette = tuple(palette) if palette else None
    for x in range(109, 113):
        for y in range(1, 6):
            pixel_color = normalize_color(image.getpixel((x, y)), palette)
            if square_distance(pixel_color, (224, 231, 248)) <= 3:
                return True
            if square_distance(pixel_color, (209, 220, 244)) <= 3:
                return True
    return False
