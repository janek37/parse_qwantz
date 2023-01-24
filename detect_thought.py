from collections import deque
from itertools import product

from box import Box
from pixels import Pixel
from simple_image import SimpleImage
from shape import get_shape, get_adjacent_pixels, get_box


def get_thought(pixel: Pixel, image: SimpleImage) -> tuple[Box, list[Pixel]] | None:
    orig_pixels = get_shape(pixel, image)
    box = get_box(orig_pixels)
    pixels: set[Pixel] = set(orig_pixels)
    for x, y in orig_pixels:
        pixels.update({Pixel(x + 1, y), Pixel(x + 2, y)})
    x_range = range(box.left + 1, box.right - 1)
    y_range = range(box.top + 1, box.bottom - 1)
    outside = set()
    outside.update(Pixel(box.left, y) for y in y_range)
    outside.update(Pixel(box.right, y) for y in y_range)
    outside.update((Pixel(x, box.top - 1) for x in x_range))
    outside.update((Pixel(x, box.bottom - 1) for x in x_range))
    non_empty_interior = False
    for x, y in product(x_range, y_range):
        if Pixel(x, y) in pixels:
            continue
        visited = set()
        to_visit = deque([Pixel(x, y)])
        while to_visit:
            current = to_visit.popleft()
            if current in visited or current in pixels or not box.includes(current):
                continue
            if current in outside:
                outside.update(visited)
                break
            visited.add(current)
            to_visit.extend(get_adjacent_pixels(current))
        else:
            non_empty_interior = True
            break
    if non_empty_interior:
        return box, sorted(orig_pixels)
