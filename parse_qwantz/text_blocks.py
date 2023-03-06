import logging
import re
from itertools import groupby
from typing import Iterable, NamedTuple

from parse_qwantz.box import Box, get_interval_distance
from parse_qwantz.fonts import Font, CharBox
from parse_qwantz.colors import Color
from parse_qwantz.hyphens import disambiguate_hyphen
from parse_qwantz.text_lines import TextLine, group_text_lines
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage

logger = logging.getLogger()


class TextBlock(NamedTuple):
    rows: list[list[TextLine]]
    bond_strengths: list[int]
    color: Color
    font: Font

    @property
    def start(self) -> Pixel:
        return self.rows[0][0].start

    @property
    def end(self) -> Pixel:
        return self.rows[-1][-1].end

    @property
    def is_bold(self) -> bool:
        return all(line.is_bold for line in self.lines)

    @property
    def box(self) -> Box:
        top = self.start.y
        bottom = self.end.y
        left = min(line[0].start.x for line in self.rows)
        right = max(line[-1].end.x for line in self.rows)
        return Box(Pixel(left, top), Pixel(right, bottom))

    @property
    def lines(self) -> Iterable[TextLine]:
        for row in self.rows:
            yield from row

    def content(self, mark_bold=True, include_font_name=False):
        char_boxes = []
        for row in self.rows:
            if char_boxes:
                if char_boxes[-1].char != '-' or char_boxes[-2].char in ' -':
                    char_boxes.append(CharBox.space(is_bold=char_boxes[-1].is_bold, is_italic=char_boxes[-1].is_italic))
                else:
                    last_words = ''
                    for char_box in char_boxes[-2::-1]:
                        if char_box.char in '.,!?" ':
                            break
                        last_words = char_box.char + last_words
                    next_words = re.match(r'[^].,!?" ]*', row[0].content).group()
                    last_word = last_words.rsplit('-', 1)[-1]
                    next_word = next_words.split('-', 1)[0]
                    if not disambiguate_hyphen(last_word, next_word):
                        char_boxes.pop()
                    else:
                        last_words += '-'
                    logger.info(f"Line ending with hyphen ({last_words}/{next_words})")
            previous_line = None
            for line in row:
                if previous_line and line.box().left - previous_line.box().right >= line.font.space_width // 2:
                    char_boxes.append(CharBox.space(is_bold=previous_line.is_bold, is_italic=previous_line.is_italic))
                char_boxes.extend(line.char_boxes)
                previous_line = line

        grouped_char_boxes = groupby(char_boxes, key=lambda cb: (cb.is_bold and mark_bold, cb.is_italic))
        text_and_weight = (
            (''.join(char_box.char for char_box in group), is_bold, is_italic)
            for (is_bold, is_italic), group in grouped_char_boxes
        )
        content = ''.join(
            mark_excluding_trailing_spaces(content, '**' if is_bold else '_') if is_bold or is_italic else content
            for content, is_bold, is_italic in text_and_weight
        )
        content = content.replace('  ', ' ')
        if include_font_name and self.font.name not in ('Regular', 'Italic'):
            content = f"({self.font.name.lower()}) {content}"
        return content

    def split(self, line1: TextLine, line2: TextLine) -> tuple["TextBlock", "TextBlock"]:
        line1_index = self.row_index(line1)
        line2_index = self.row_index(line2)
        index1, index2 = sorted((line1_index, line2_index))
        _, split_index = min((self.bond_strengths[i], i) for i in range(index1, index2))
        block1 = TextBlock(self.rows[:split_index+1], self.bond_strengths[:split_index], self.color, self.font)
        block2 = TextBlock(self.rows[split_index+1:], self.bond_strengths[split_index+1:], self.color, self.font)
        if line1_index < line2_index:
            return block1, block2
        else:
            return block2, block1

    def row_index(self, line: TextLine) -> int:
        return next(i for i, row in enumerate(self.rows) if line in row)

    def __str__(self):
        return self.content()

    def __hash__(self):
        return id(self)


def mark_excluding_trailing_spaces(s: str, marker: str) -> str:
    trailing_spaces = re.search(r" *$", s).group()
    return f'{marker}{s.rstrip()}{marker}{trailing_spaces}'


def get_text_blocks(text_lines: list[TextLine], image: SimpleImage) -> Iterable[TextBlock]:
    grouped_lines = group_text_lines(text_lines, same_font=True, long_space=True)
    while grouped_lines:
        new_block = [grouped_lines[0]]
        bond_strengths = []
        font = grouped_lines[0][0].font
        new_lines: list[list[TextLine]] = []
        for text_line_group in grouped_lines[1:]:
            bond_strength = fit_to_block(text_line_group, new_block[-1], font)
            if bond_strength is not None:
                new_block.append(text_line_group)
                bond_strengths.append(bond_strength)
            else:
                new_lines.append(text_line_group)
        grouped_lines = new_lines
        found_pixel = new_block[0][0].find_pixel()
        color = image.pixels[found_pixel] if found_pixel else Color.WHITE
        yield TextBlock(new_block, bond_strengths, color, font)


def fit_to_block(line_group: list[TextLine], previous_group: list[TextLine], font: Font) -> int | None:
    if line_group[0].font.group != font.group:
        return None
    first_box = line_group[0].box()
    last_box = line_group[-1].box()
    left = first_box.left
    right = last_box.right
    top = min(first_box.top, last_box.top)
    if all(line.is_bold for line in previous_group) and not any(line.contains_bold for line in line_group):
        return None
    previous_first_box = previous_group[0].box()
    previous_last_box = previous_group[-1].box()
    previous_left = previous_first_box.left
    previous_right = previous_first_box.right
    previous_bottom = max(previous_first_box.bottom, previous_last_box.bottom)
    if get_interval_distance(
        (left, right),
        (previous_left, previous_right),
    ) != 0:
        return None
    previous_height = font.height
    previous_width = font.space_width
    if previous_bottom - 1 <= top <= previous_bottom + previous_height // 6:
        bond_strength = 0
        if previous_left == left:
            bond_strength += 5
        elif (previous_left - left) % previous_width == 0 and font.is_mono:
            bond_strength += 3
        if top <= previous_bottom:
            bond_strength += 10
        if top >= previous_bottom + previous_height:
            bond_strength -= 10
        return bond_strength
    return None
