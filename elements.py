from logging import getLogger

from box import Box
from character_shapes import ALL_FONTS
from detect_lines import Line, get_line
from detect_text import TextLine, try_text_line
from detect_thought import get_thought
from pixels import Pixel
from shape import get_shape
from simple_image import SimpleImage

logger = getLogger()


def get_elements(image: SimpleImage) -> tuple[list[Line], list[Box], list[TextLine], list[list[Pixel]]]:
    text_lines: list[TextLine] = []
    lines: list[Line] = []
    thoughts: list[Box] = []
    unmatched: list[list[Pixel]] = []
    sorted_pixels = sorted(image.pixels)
    while sorted_pixels:
        pixel = sorted_pixels[0]
        pixels = set(sorted_pixels)
        tmp_image = SimpleImage(
            width=image.width,
            height=image.height,
            pixels={pixel: color for pixel, color in image.pixels.items() if pixel in pixels},
        )
        for font in ALL_FONTS:
            text_line = try_text_line(pixel, tmp_image, font)
            if text_line:
                text_lines.append(text_line)
                sorted_pixels = remove_boxes(sorted_pixels, [char_box.box for char_box in text_line.character_boxes])
                break
        else:
            result = get_line(pixel, tmp_image)
            if result:
                line, line_pixels = result
                lines.append(line)
                sorted_pixels = remove_subsequence(sorted_pixels, line_pixels)
            elif result := get_thought(pixel, tmp_image):
                box, thought_pixels = result
                thoughts.append(box)
                sorted_pixels = remove_subsequence(sorted_pixels, thought_pixels)
            else:
                logger.warning(f"No match found for shape at {(pixel.x, pixel.y)}")
                unmatched_pixels = sorted(get_shape(pixel, tmp_image))
                unmatched.append(unmatched_pixels)
                sorted_pixels = remove_subsequence(sorted_pixels, unmatched_pixels)
    return lines, thoughts, sorted(text_lines, key=lambda l: (l.start.y, l.start.x)), unmatched


def remove_boxes(sorted_pixels: list[Pixel], boxes: list[Box]) -> list[Pixel]:
    box_iter = iter(boxes)
    box = next(box_iter)
    new_pixels = []
    pass_through = False
    for pixel in sorted_pixels:
        while not pass_through and pixel.x >= box.right:
            try:
                box = next(box_iter)
            except StopIteration:
                pass_through = True
        if pass_through or not box.includes(pixel):
            new_pixels.append(pixel)
    return new_pixels


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
