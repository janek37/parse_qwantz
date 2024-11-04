from functools import reduce
from logging import getLogger

from parse_qwantz.box import Box
from parse_qwantz.fonts import ALL_FONTS
from parse_qwantz.lines import Line, get_line
from parse_qwantz.match_lines import Character, Direction
from parse_qwantz.text_lines import TextLine, try_text_line, cleanup_text_lines
from parse_qwantz.detect_thought import get_thought
from parse_qwantz.pixels import Pixel, remove_subsequence
from parse_qwantz.shape import get_shape
from parse_qwantz.simple_image import SimpleImage

logger = getLogger()


def get_elements(
    image: SimpleImage
) -> tuple[list[Line], list[int], list[Box], list[TextLine], list[Character], list[list[Pixel]]]:
    text_lines: list[TextLine] = []
    lines: list[Line] = []
    line_widths: list[int] = []
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
        text_line_candidates = [text_line for text_line in text_line_candidates if text_line]
        longest_candidate = max(text_line_candidates, key=lambda tl: tl[0].box().right, default=None)
        # UGLY SPECIAL CASE AHOY
        if longest_candidate and longest_candidate[0].content == "-" and longest_candidate[0].font.name == "Italic":
            try:
                longest_candidate = next(c for c in text_line_candidates if c[0].font.name == "Regular")
            except StopIteration:
                pass
        if longest_candidate:
            longest_line, warnings = longest_candidate
            for warning in warnings:
                logger.warning(warning)
            text_lines.append(longest_line)
            pixels = reduce(set.union, (char_box.pixels for char_box in longest_line.char_boxes))
            sorted_pixels = remove_subsequence(sorted_pixels, sorted(pixels))
        else:
            result = get_line(pixel, tmp_image)
            if result:
                line, line_pixels, width = result
                lines.append(line)
                line_widths.append(width)
                sorted_pixels = remove_subsequence(sorted_pixels, line_pixels)
            elif result := get_batman(pixel, tmp_image):
                batman_box, batman_pixels, batman_direction = result
                extra_characters.append(Character("Floating Batman head", (batman_box,), batman_direction))
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
    return lines, line_widths, thoughts, cleanup_text_lines(text_lines), extra_characters, unmatched


def get_batman(pixel: Pixel, image: SimpleImage) -> tuple[Box, list[Pixel], Direction] | None:
    pixels = get_shape(pixel, image)
    if len(pixels) != 187:
        return None
    if Pixel(pixel.x + 11, pixel.y - 7) in pixels and Pixel(pixel.x + 11, pixel.y - 8) not in pixels:
        return Box(Pixel(pixel.x + 1, pixel.y - 7), Pixel(pixel.x + 15, pixel.y + 11)), sorted(pixels), Direction.LEFT
    if Pixel(pixel.x + 2, pixel.y - 17) in pixels and Pixel(pixel.x + 2, pixel.y - 18) not in pixels:
        return Box(Pixel(pixel.x, pixel.y - 17), Pixel(pixel.x + 14, pixel.y + 1)), sorted(pixels), Direction.RIGHT
    return None
