from functools import reduce
from logging import getLogger

from parse_qwantz.box import Box
from parse_qwantz.fonts import ALL_FONTS
from parse_qwantz.lines import Line, get_line
from parse_qwantz.match_lines import Character
from parse_qwantz.text_lines import TextLine, try_text_line, cleanup_text_lines
from parse_qwantz.detect_thought import get_thought
from parse_qwantz.pixels import Pixel, remove_subsequence
from parse_qwantz.shape import get_shape
from parse_qwantz.simple_image import SimpleImage

logger = getLogger()


def get_elements(
    image: SimpleImage
) -> tuple[list[Line], list[Box], list[TextLine], list[Character], list[list[Pixel]]]:
    text_lines: list[TextLine] = []
    lines: list[Line] = []
    thoughts: list[Box] = []
    unmatched: list[list[Pixel]] = []
    sorted_pixels = sorted(image.pixels)
    extra_characters = []
    while sorted_pixels:
        pixel = sorted_pixels[0]
        pixels = set(sorted_pixels)
        tmp_image = SimpleImage(
            width=image.width,
            height=image.height,
            pixels={pixel: color for pixel, color in image.pixels.items() if pixel in pixels},
        )
        text_line_candidates = (try_text_line(pixel, tmp_image, font) for font in ALL_FONTS)
        text_line_candidates = (text_line for text_line in text_line_candidates if text_line)
        longest_candidate = max(text_line_candidates, key=lambda tl: len(tl.char_boxes), default=None)
        if longest_candidate:
            text_lines.append(longest_candidate)
            pixels = reduce(set.union, (char_box.pixels for char_box in longest_candidate.char_boxes))
            sorted_pixels = remove_subsequence(sorted_pixels, sorted(pixels))
        else:
            result = get_line(pixel, tmp_image)
            if result:
                line, line_pixels = result
                lines.append(line)
                sorted_pixels = remove_subsequence(sorted_pixels, line_pixels)
            elif result := get_batman(pixel, tmp_image):
                batman_box, batman_pixels = result
                extra_characters.append(Character("Floating Batman head", batman_box, can_think=False))
                sorted_pixels = remove_subsequence(sorted_pixels, batman_pixels)
            elif result := get_thought(pixel, tmp_image):
                box, thought_pixels = result
                thoughts.append(box)
                sorted_pixels = remove_subsequence(sorted_pixels, thought_pixels)
            else:
                unmatched_pixels = sorted(get_shape(pixel, tmp_image))
                unmatched.append(unmatched_pixels)
                sorted_pixels = remove_subsequence(sorted_pixels, unmatched_pixels)
                logger.warning(f"No match found for shape at {(pixel.x, pixel.y)} ({len(unmatched_pixels)} pixels)")
                if len(unmatched) == 5:
                    logger.warning("At least five unmatched objects detected, aborting")
                    break
    return lines, thoughts, cleanup_text_lines(text_lines), extra_characters, unmatched


def get_batman(pixel: Pixel, image: SimpleImage) -> tuple[Box, list[Pixel]] | None:
    pixels = get_shape(pixel, image)
    if len(pixels) != 187:
        return None
    if Pixel(pixel.x + 11, pixel.y - 7) in pixels and Pixel(pixel.x + 11, pixel.y - 8) not in pixels:
        return Box(Pixel(pixel.x, pixel.y - 7), Pixel(pixel.x + 14, pixel.y + 11)), sorted(pixels)
    if Pixel(pixel.x + 2, pixel.y - 17) in pixels and Pixel(pixel.x + 2, pixel.y - 18) not in pixels:
        return Box(Pixel(pixel.x, pixel.y - 7), Pixel(pixel.x + 14, pixel.y + 11)), sorted(pixels)
    return None
