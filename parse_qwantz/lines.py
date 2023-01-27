from itertools import groupby, product

from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage
from parse_qwantz.shape import get_shape, get_box

Line = tuple[Pixel, Pixel]


def get_line(pixel: Pixel, image: SimpleImage) -> tuple[Line, list[Pixel]] | None:
    pixels = get_shape(pixel, image)
    if len(set(pixels.values())) != 1:
        return None
    (x_min, y_min), (right, bottom) = get_box(pixels)
    x_max = right - 1
    y_max = bottom - 1
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
    if (end1.x - end2.x)**2 + (end1.y - end2.y)**2 < 10:
        return None
    sorted_pixels = sorted(pixels)
    slices = [list(y for x, y in group) for key, group in groupby(sorted_pixels, key=lambda px: px.x)]
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
