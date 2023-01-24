from itertools import chain, groupby
from typing import Iterable, NamedTuple

from box import Box, get_interval_distance
from fonts import Font
from colors import Color
from text_lines import TextLine, try_text_line
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
    def is_bold(self) -> bool:
        return all(line.is_bold for line in self.lines)

    @property
    def box(self) -> Box:
        top = self.start.y
        bottom = self.end.y
        left = min(line.start.x for line in self.lines)
        right = max(line.x_end for line in self.lines)
        return Box(Pixel(left, top), Pixel(right, bottom))

    def content(self, mark_bold=True):
        if not mark_bold:
            line_contents = (line.content for line in self.lines)
        else:
            words = chain.from_iterable(line.words for line in self.lines)
            grouped_words = groupby(words, key=lambda w: w.is_bold)
            text_and_weight = (
                (' '.join(word.content for word in group), is_bold)
                for is_bold, group in grouped_words
            )
            line_contents = (
                f'**{content}**' if is_bold else content
                for content, is_bold in text_and_weight
            )
            line_contents = list(line_contents)
        return ' '.join(line_contents).replace('  ', ' ')

    def __str__(self):
        if self.font.name == 'Regular':
            return self.content()
        else:
            return f"[{self.font}] {self.content()}"


def get_text_blocks(text_lines: list[TextLine], image: SimpleImage) -> Iterable[TextBlock]:
    grouped_lines = group_text_lines(text_lines)
    text_lines = sorted(
        chain.from_iterable(join_text_lines(group, image) for group in grouped_lines),
        key=lambda l: (l.start.y, l.start.x)
    )
    while text_lines:
        new_block = [text_lines[0]]
        font = text_lines[0].font
        new_lines: list[TextLine] = []
        for text_line in text_lines[1:]:
            append = False
            if text_line.font == font:
                text_box = text_line.box()
                previous_line = new_block[-1]
                bold_mismatch = (
                    (previous_line.is_bold and not text_line.contains_bold)
                    or (not previous_line.contains_bold and text_line.is_bold)
                )
                if not bold_mismatch:
                    previous_box = previous_line.box()
                    intervals_intersect = get_interval_distance(
                        (text_box.left, text_box.right),
                        (previous_box.left, previous_box.right),
                    ) == 0
                    ceiling = previous_box.bottom
                    if ceiling - 1 <= text_box.top <= ceiling + 1 and intervals_intersect:
                        append = True
            if append:
                new_block.append(text_line)
            else:
                new_lines.append(text_line)
        text_lines = new_lines
        color = image.find_color(new_block[0].char_boxes[0].box)
        yield TextBlock(new_block, color, font)


def group_text_lines(text_lines: list[TextLine]) -> list[list[TextLine]]:
    grouped_text_lines = []
    used: set[int] = set()
    for text_line in text_lines:
        if id(text_line) in used:
            continue
        used.add(id(text_line))
        group = [text_line]
        box = text_line.box()
        for other_text_line in text_lines:
            if id(other_text_line) in used:
                continue
            other_box = other_text_line.box()
            if abs(box.top - other_box.top) <= 1 or abs(box.bottom - other_box.bottom) <= 1:
                distance = other_box.left - box.right
                if -1 <= distance <= max(group[-1].font.width, other_text_line.font.width) * 2 + 1:
                    group.append(other_text_line)
                    used.add(id(other_text_line))
        grouped_text_lines.append(group)
    return grouped_text_lines


def join_text_lines(text_lines: list[TextLine], image: SimpleImage) -> list[TextLine]:
    if len(text_lines) == 1:
        return text_lines
    for font in (line.font for line in text_lines):
        if font == text_lines[0].font:
            continue
        first_pixel = image.find_pixel(text_lines[0].char_boxes[0].box)
        if joined_text_line := try_text_line(first_pixel, image, font):
            joined_box = joined_text_line.box()
            if abs(joined_box.right - text_lines[-1].box().right) < font.width // 2:
                return [joined_text_line]
    return text_lines
