from collections import deque
from itertools import product

from parse_qwantz.box import Box
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage
from parse_qwantz.shape import get_shape, get_adjacent_pixels, get_box


def get_thought(pixel: Pixel, image: SimpleImage) -> tuple[Box, list[Pixel]] | None:
    orig_pixels = get_shape(pixel, image)
    box = get_box(orig_pixels)
    if any(x == 0 for x, y in orig_pixels) and any(x == image.width - 1 for x, y in orig_pixels):
        if len(set(y for x, y in orig_pixels)) > 2:
            box = Box(Pixel(0, 0), box.bottom_right)
            return box, sorted(orig_pixels)
        else:
            return None
    tripled_pixels: set[Pixel] = set(orig_pixels)
    for x, y in orig_pixels:
        tripled_pixels.update({Pixel(x + 1, y), Pixel(x + 2, y)})
    if is_thought(tripled_pixels, box, image) or is_thought(set(orig_pixels), box, image):
        return box, sorted(orig_pixels)


def is_thought(pixels: set[Pixel], box: Box, image: SimpleImage) -> bool:
    x_range = range(box.left, box.right)
    y_range = range(box.top, box.bottom)
    outside = set()
    outside.update(Pixel(box.left, y) for y in y_range)
    outside.update(Pixel(box.right - 1, y) for y in y_range)
    outside.update((Pixel(x, box.top) for x in x_range))
    outside.update((Pixel(x, box.bottom - 1) for x in x_range))
    for x, y in product(x_range, y_range):
        if Pixel(x, y) in pixels:
            continue
        visited = set()
        to_visit = deque([Pixel(x, y)])
        while to_visit:
            current = to_visit.popleft()
            on_image_border = image.is_on_edge(current)
            if current in visited or current in pixels or not box.includes(current) or on_image_border:
                continue
            if current in outside:
                outside.update(visited)
                break
            visited.add(current)
            to_visit.extend(get_adjacent_pixels(current))
        else:
            return True
    return False
