from functools import reduce
from logging import getLogger

from parse_qwantz.box import Box
from parse_qwantz.fonts import ALL_FONTS
from parse_qwantz.lines import Line, get_line
from parse_qwantz.text_lines import TextLine, try_text_line, cleanup_text_lines
from parse_qwantz.detect_thought import get_thought
from parse_qwantz.pixels import Pixel, remove_subsequence
from parse_qwantz.shape import get_shape
from parse_qwantz.simple_image import SimpleImage

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
                pixels = reduce(set.union, (char_box.pixels for char_box in text_line.char_boxes))
                sorted_pixels = remove_subsequence(sorted_pixels, sorted(pixels))
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
                if len(unmatched) == 5:
                    logger.warning("At least five unmatched objects detected, aborting")
                    break
    return lines, thoughts, cleanup_text_lines(text_lines, image), unmatched
