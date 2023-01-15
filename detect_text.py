from typing import Iterable, NamedTuple

from character_shapes import Font
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

    @property
    def start(self):
        return self.lines[0].start

    @property
    def content(self):
        return ' '.join(line.content for line in self.lines).replace('  ', ' ')

    def __str__(self):
        return f"{self.start} [{self.font}] {self.content}"


def get_text_blocks(text_lines: list[TextLine], image: SimpleImage) -> Iterable[TextBlock]:
    while text_lines:
        new_block = [text_lines[0]]
        font = text_lines[0].font
        new_lines: list[TextLine] = []
        for text_line in text_lines[1:]:
            if text_line.font == font:
                (x, y), (x_end, y_end) = text_line.box()
                line0 = new_block[-1]
                (x0, y0), (x1, y1) = line0.box()
                interval0, interval1 = sorted([(x, x_end), (x0, x1)])
                if y == y1 and interval0[1] > interval1[0]:
                    new_block.append(text_line)
                else:
                    new_lines.append(text_line)
            else:
                new_lines.append(text_line)
        text_lines = new_lines
        color = image.find_color(new_block[0].box())
        yield TextBlock(new_block, color, font)


def try_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    x0, y0 = start
    for x in range(x0, x0 - font.width + 1, -1):
        for y in range(y0, y0 - font.height + 1, -1):
            line = get_text_line((x, y), image, font)
            if line:
                return line


def get_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    text = font.get_char(start, image=image)
    if text in (' ', None):
        return None
    spaces = 0
    x, y = start
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
    return TextLine(start, text, font)
