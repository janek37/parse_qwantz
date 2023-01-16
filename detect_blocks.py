from typing import Iterable, NamedTuple

from character_shapes import Font
from colors import Color
from detect_text import TextLine
from pixels import SimpleImage


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
        if self.font.name == 'Regular':
            return self.content
        else:
            return f"[{self.font}] {self.content}"


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
                if y in (y1, y1 + 1) and interval0[1] > interval1[0]:
                    new_block.append(text_line)
                else:
                    new_lines.append(text_line)
            else:
                new_lines.append(text_line)
        text_lines = new_lines
        color = image.find_color(new_block[0].box())
        yield TextBlock(new_block, color, font)
