from typing import Iterable, NamedTuple

from character_shapes import Font, FONT_GROUPS
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
        if all(line.font.is_bold for line in self.lines):
            line_contents = (line.content for line in self.lines)
        else:
            line_contents = (f'*{line.content}*' if line.font.is_bold else line.content for line in self.lines)
        return ' '.join(line_contents).replace('  ', ' ')

    def __str__(self):
        if self.font.name == 'Regular':
            return self.content
        else:
            return f"[{self.font}] {self.content}"


def get_text_blocks(text_lines: list[TextLine], image: SimpleImage) -> Iterable[TextBlock]:
    while text_lines:
        new_block = [text_lines[0]]
        font = text_lines[0].font
        del text_lines[0]
        while True:
            new_lines: list[TextLine] = []
            new_block_lines = []
            for text_line in text_lines:
                if text_line.font in FONT_GROUPS[font.name]:
                    (x, y), (x_end, y_end) = text_line.box()
                    line0 = new_block[-1]
                    (x0, y0), (x1, y1) = line0.box()
                    interval0, interval1 = sorted([(x, x_end), (x0, x1)])
                    if y1 - 1 <= y <= y1 + 1 and interval0[1] > interval1[0]:
                        new_block_lines.append(text_line)
                    else:
                        new_lines.append(text_line)
                else:
                    new_lines.append(text_line)
            new_block.extend(new_block_lines)
            text_lines = new_lines
            if not new_block_lines:
                break
        color = image.find_color(new_block[0].character_boxes[0].box)
        yield TextBlock(new_block, color, font)
