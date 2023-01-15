from itertools import groupby, product

from colors import Color
from pixels import Pixel, SimpleImage

Line = tuple[Pixel, Pixel]


def get_line(pixel: Pixel, image: SimpleImage) -> tuple[Line, list[Pixel]] | None:
    pixels = get_shape(pixel, image)
    if len(set(pixels.values())) != 1:
        return None
    x_min = min(x for x, y in pixels)
    x_max = max(x for x, y in pixels)
    y_min = min(y for x, y in pixels)
    y_max = max(y for x, y in pixels)
    # \ or /
    if (x_min, y_min) in pixels and (x_max, y_max) in pixels:
        end1 = (x_min, y_min)
        end2 = (x_max, y_max)
        forward = True
    elif (x_min, y_max) in pixels and (x_max, y_min) in pixels:
        end1 = (x_min, y_max)
        end2 = (x_max, y_min)
        forward = False
    else:
        return None
    sorted_pixels = sorted(pixels)
    slices = [list(y for x, y in group) for key, group in groupby(sorted_pixels, key=lambda px: px[0])]
    # all slices are single intervals
    for s in slices:
        if not all(y1 + 1 == y2 for y1, y2 in zip(s, s[1:])):
            return None
    # slices are monotonic
    for slice1, slice2 in zip(slices, slices[1:]):
        if forward and (slice1[0] > slice2[0] or slice1[-1] > slice2[-1]):
            return None
        if not forward and (slice1[0] < slice2[0] or slice1[-1] < slice2[-1]):
            return None
    # must contain 2x2 square
    if not any(
        (x + 1, y) in pixels and (x, y + 1) in pixels and (x + 1, y + 1) in pixels
        for x, y in pixels
    ):
        return None
    for x, y in pixels:
        for i, j in product(range(3), range(3)):
            if (x + i, y + j) not in pixels:
                break
        else:
            # contains 3x3 square
            return None
    return (end1, end2), sorted_pixels


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
    return [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
