from typing import Iterable, NamedTuple

from box import Box, get_interval_distance
from character_shapes import Font, FONT_GROUPS
from colors import Color
from detect_text import TextLine
from pixels import Pixel
from simple_image import SimpleImage


class TextBlock(NamedTuple):
    lines: list[TextLine]
    color: Color
    font: Font

    @property
    def start(self) -> Pixel:
        return self.lines[0].start

    @property
    def end(self) -> Pixel:
        return self.lines[-1].end

    @property
    def box(self) -> Box:
        top = self.start.y
        bottom = self.end.y
        left = min(line.start.x for line in self.lines)
        right = max(line.x_end for line in self.lines)
        return Box(Pixel(left, top), Pixel(right, bottom))

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
                    text_box = text_line.box()
                    previous_line = new_block[-1]
                    previous_box = previous_line.box()
                    intervals_intersect = get_interval_distance(
                        (text_box.left, text_box.right),
                        (previous_box.left, previous_box.right),
                    ) == 0
                    ceiling = previous_box.bottom
                    if ceiling - 1 <= text_box.top <= ceiling + 1 and intervals_intersect:
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
