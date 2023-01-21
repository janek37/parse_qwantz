from itertools import groupby, product

from pixels import Pixel
from simple_image import SimpleImage
from shape import get_shape

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
        end1 = Pixel(x_min, y_min)
        end2 = Pixel(x_max, y_max)
        forward = True
    elif (x_min, y_max) in pixels and (x_max, y_min) in pixels:
        end1 = Pixel(x_min, y_max)
        end2 = Pixel(x_max, y_min)
        forward = False
    else:
        return None
    if end1 == end2:
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
    for x, y in pixels:
        for i, j in product(range(3), range(3)):
            if (x + i, y + j) not in pixels:
                break
        else:
            # contains 3x3 square
            return None
    return (end1, end2), sorted_pixels
