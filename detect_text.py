from typing import Iterable, NamedTuple

from PIL import Image

from character_shapes import REGULAR_FONT, Font, BOLD_FONT
from colors import Color
from pixels import Pixel, SimpleImage


class TextLine(NamedTuple):
    start: Pixel
    content: str
    font: Font

    def box(self) -> tuple[Pixel, Pixel]:
        x, y = self.start
        return self.start, (self.x_end(), y + self.font.height)

    def x_end(self):
        return self.start[0] + self.font.width * len(self.content)


class TextBlock(NamedTuple):
    lines: list[TextLine]
    color: Color
    font: Font


def get_text_blocks(image: SimpleImage, font: Font) -> Iterable[TextBlock]:
    lines = get_text_lines(image, font)
    while lines:
        new_block = [lines[0]]
        new_lines: list[TextLine] = []
        for line in lines[1:]:
            (x, y), (x_end, y_end) = line.box()
            line0 = new_block[-1]
            (x0, y0), (x1, y1) = line0.box()
            interval0, interval1 = sorted([(x, x_end), (x0, x1)])
            if y == y1 and interval0[1] > interval1[0]:
                new_block.append(line)
            else:
                new_lines.append(line)
        lines = new_lines
        color = image.find_color(new_block[0].box())
        yield TextBlock(new_block, color, font)


def get_text_lines(image: SimpleImage, font: Font) -> list[TextLine]:
    lines = []
    for y in range(image.height - font.height + 1):
        x = 0
        while x < image.width - font.width + 1:
            for line in lines:
                l_x, l_y = line.start
                if l_x - font.width < x <= l_x and y - l_y < font.height:
                    x = line.x_end()
                    break
            if x >= image.width - font.width + 1:
                break
            line = get_text_line((x, y), image, font)
            if line and line.content not in ".'`,|":
                lines.append(line)
                x = line.x_end()
            x += 1
    return lines


def get_text_line(pixel: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    text = font.get_char(pixel, image=image)
    if text in (' ', None):
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
                last_char = text[-1]
                if last_char == '"':
                    if len(text) < 1:
                        break
                    last_char = text[-2]
                if last_char not in '.!?':
                    break
        elif char is not None:
            if spaces > 0:
                text += ' ' * spaces
                spaces = 0
            text += char
        else:
            break
    return TextLine(pixel, text, font)


if __name__ == '__main__':
    import sys
    img = SimpleImage.from_image(Image.open(sys.argv[1]))
    for block in get_text_blocks(img, REGULAR_FONT):
        print(' '.join(line.content for line in block.lines).replace('  ', ' '))
    for block in get_text_blocks(img, BOLD_FONT):
        print(' '.join(line.content for line in block.lines).replace('  ', ' '))
