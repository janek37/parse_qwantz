from character_shapes import ALL_FONTS
from detect_lines import Line, get_line
from detect_text import TextLine, try_text_line
from pixels import SimpleImage, Pixel


class NoMatchFound(Exception):
    pass


def get_elements(image: SimpleImage) -> tuple[list[Line], list[TextLine]]:
    text_lines: list[TextLine] = []
    lines: list[Line] = []
    sorted_pixels = sorted(image.pixels)
    while sorted_pixels:
        pixel = sorted_pixels[0]
        for font in ALL_FONTS:
            text_line = try_text_line(pixel, image, font)
            if text_line:
                text_lines.append(text_line)
                sorted_pixels = remove_box(sorted_pixels, text_line.box())
                break
        else:
            result = get_line(pixel, image)
            if result:
                line, line_pixels = result
                lines.append(line)
                sorted_pixels = remove_subsequence(sorted_pixels, line_pixels)
            else:
                raise NoMatchFound(f"No match found for pixel {pixel}")
    return lines, sorted(text_lines, key=lambda l: (l.start[1], l.start[0]))


def remove_box(sorted_pixels: list[Pixel], box: tuple[Pixel, Pixel]) -> list[Pixel]:
    (x0, y0), (x1, y1) = box
    return [(x, y) for x, y in sorted_pixels if not (x0 <= x < x1 and y0 <= y < y1)]


def remove_subsequence(sorted_pixels: list[Pixel], subsequence: list[Pixel]) -> list[Pixel]:
    sub_iter = iter(subsequence)
    next_pixel = next(sub_iter)
    pixels = []
    for pixel in sorted_pixels:
        if pixel == next_pixel:
            try:
                next_pixel = next(sub_iter)
            except StopIteration:
                next_pixel = None
        else:
            pixels.append(pixel)
    return pixels


if __name__ == '__main__':
    import sys
    from PIL import Image
    from detect_text import get_text_blocks
    img = SimpleImage.from_image(Image.open(sys.argv[1]))
    lins, txt_lines = get_elements(img)
    for lin in lins:
        print(lin[0], '->', lin[1])
    for block in get_text_blocks(txt_lines, img):
        print(block.font, block.content)
