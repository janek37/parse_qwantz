from typing import Iterable

from PIL import Image

from character_shapes import REGULAR_FONT, Font, BOLD_FONT
from pixels import Pixel, SimpleImage


def get_text_blocks(image: SimpleImage, font: Font) -> Iterable[list[tuple[Pixel, str]]]:
    lines = get_text_lines(image, font)
    while lines:
        new_block = [lines[0]]
        new_lines = []
        for (x, y), line in lines[1:]:
            (x0, y0), line0 = new_block[-1]
            x1 = x0 + font.width * len(line0)
            x_end = x * font.width * len(line)
            interval0, interval1 = sorted([(x, x_end), (x0, x1)])
            if y == y0 + font.height and interval0[1] > interval1[0]:
                new_block.append(((x, y), line))
            else:
                new_lines.append(((x, y), line))
        lines = new_lines
        yield new_block


def get_text_lines(image: SimpleImage, font: Font) -> list[tuple[Pixel, str]]:
    lines = []
    for y in range(image.height - font.height + 1):
        x = 0
        while x < image.width - font.width + 1:
            for (l_x, l_y), line in lines:
                if l_x - font.width < x <= l_x and y - l_y < font.height:
                    x = l_x + font.width * len(line)
                    break
            if x >= image.width - font.width + 1:
                break
            line = get_line((x, y), image, font)
            if line and line not in ".'`,|":
                lines.append(((x, y), line))
                x += font.width * len(line)
            x += 1
    return lines


def get_line(pixel: Pixel, image: SimpleImage, font: Font) -> str | None:
    line = font.get_char(pixel, image=image)
    if line in (' ', None):
        return None
    spaces = 0
    x, y = pixel
    while True:
        x += font.width
        if x > image.width - font.width:
            break
        char = font.get_char((x, y), image)
        if char == ' ':
            spaces += 1
            if spaces > 2:
                break
            if spaces == 2:
                last_char = line[-1]
                if last_char == '"':
                    if len(line) < 1:
                        break
                    last_char = line[-2]
                if last_char not in '.!?':
                    break
        elif char is not None:
            if spaces > 0:
                line += ' ' * spaces
                spaces = 0
            line += char
        else:
            break
    return line


if __name__ == '__main__':
    import sys
    img = SimpleImage.from_image(Image.open(sys.argv[1]))
    for block in get_text_blocks(img, REGULAR_FONT):
        print(' '.join(line for _, line in block).replace('  ', ' '))
    for block in get_text_blocks(img, BOLD_FONT):
        print(' '.join(line for _, line in block).replace('  ', ' '))
