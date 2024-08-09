import logging
import re
from dataclasses import dataclass
from functools import cached_property, cmp_to_key
from itertools import groupby
from typing import Iterable

from parse_qwantz.box import Box, get_interval_distance
from parse_qwantz.fonts import Font, CharBox
from parse_qwantz.colors import Color
from parse_qwantz.hyphens import disambiguate_hyphen
from parse_qwantz.text_lines import TextLine, group_text_lines
from parse_qwantz.pixels import Pixel

logger = logging.getLogger()


@dataclass
class TextBlock:
    rows: list[list[TextLine]]
    alignments: list["Alignment"]
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
    def is_italic(self) -> bool:
        return all(line.is_italic for line in self.lines)

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

    @cached_property
    def bond_strengths(self) -> list[int]:
        return [alignment.strength for alignment in self.alignments]

    def content(self, mark_bold=True, mark_italic=True, include_font_name=False):
        char_boxes = []
        for row in self.rows:
            row_char_boxes = list(self.get_row_charboxes(row))
            row_content = "".join(char_box.char for char_box in row_char_boxes)
            if char_boxes:
                if char_boxes[-1].char == '-' and char_boxes[-2].char not in ' -':
                    if row_content.endswith("-") and " " not in row_content:
                        logger.warning("Multiple hyphenation")
                    last_words = ''
                    for char_box in char_boxes[-2::-1]:
                        if char_box.char in '.,!?"#(/ ':
                            break
                        last_words = char_box.char + last_words
                    if last_words.startswith("'"):
                        last_words = last_words[1:]
                    next_words = re.match(r'[^].,!?"\' :;)/]*', row_content).group()
                    if not disambiguate_hyphen(last_words.split("-"), next_words.strip("-").split("-")):
                        char_boxes.pop()
                elif (
                    not (row_content.startswith("+") and row_content[1] != " ")
                    and not (len(char_boxes) > 1 and char_boxes[-1].char in "/|" and char_boxes[-2].char != " ")
                    and len(set(cb.char.lower() for cb in char_boxes[-2:]) | set(row_content[:2].lower())) != 1
                    and {char_boxes[-1].char.lower()} | set(row_content[:2].lower()) != {'h'}
                ):
                    char_boxes.append(CharBox.space(is_bold=char_boxes[-1].is_bold, is_italic=char_boxes[-1].is_italic))
            char_boxes.extend(row_char_boxes)

        grouped_char_boxes = groupby(
            char_boxes, key=lambda cb: (cb.is_bold and mark_bold, cb.is_italic and mark_italic)
        )
        text_and_weight = (
            (''.join(char_box.char for char_box in group), is_bold, is_italic)
            for (is_bold, is_italic), group in grouped_char_boxes
        )
        content = ''.join(
            mark_excluding_trailing_spaces(content, '◖◗' if is_bold else '▹◃') if is_bold or is_italic else content
            for content, is_bold, is_italic in text_and_weight
        )
        content = content.replace('  ', ' ')
        if include_font_name and self.font.display_name is not None:
            content = f"〚{self.font.display_name}〛 {content}"
        return content

    @staticmethod
    def get_row_charboxes(row: list[TextLine]) -> Iterable[CharBox]:
        previous_line = None
        for line in row:
            if previous_line and line.box().left - previous_line.box().right >= line.font.space_width // 2:
                yield CharBox.space(is_bold=previous_line.is_bold, is_italic=previous_line.is_italic)
            yield from line.char_boxes
            previous_line = line

    def unambiguous_words(self) -> Iterable[str]:
        row_contents = []
        for row in self.rows:
            row_content = ""
            previous_line = None
            for line in row:
                if previous_line and line.box().left - previous_line.box().right >= line.font.space_width // 2:
                    row_content += " "
                row_content += line.content
                previous_line = line
            row_contents.append(row_content.lower())
        was_hyphen = False
        for row_content in row_contents:
            is_hyphen = row_content[-1] == '-' and row_content[-2] not in ' -'
            words = re.findall(r"\w+", row_content)
            if was_hyphen and row_content[0].isalnum():
                del words[0]
            if is_hyphen and words:
                del words[-1]
            yield from words
            if was_hyphen:
                row_content = "-" + row_content
            yield from re.findall(r"(?<![-\w])\w+(?:-\w+)+(?![-\w])", row_content)
            was_hyphen = is_hyphen

    def split(self, line1: TextLine, line2: TextLine) -> tuple["TextBlock", "TextBlock", "Alignment"]:
        line1_index = self.row_index(line1)
        line2_index = self.row_index(line2)
        index1, index2 = sorted((line1_index, line2_index))
        breaking_strength, split_index = min(
            ((self.bond_strengths[i], i) for i in range(index1, index2)),
            key=lambda p: (p[0], -p[1]),
        )
        if self.bond_strengths[index1:index2].count(breaking_strength) > 1:
            logger.warning(f"Non-unique breaking point for splitting (strength: {breaking_strength})")
        block1 = TextBlock(self.rows[:split_index+1], self.alignments[:split_index], self.color, self.font)
        block2 = TextBlock(self.rows[split_index+1:], self.alignments[split_index+1:], self.color, self.font)
        if line1_index < line2_index:
            return block1, block2, self.alignments[split_index]
        else:
            return block2, block1, self.alignments[split_index]

    def alignment(self, line1: TextLine, line2: TextLine) -> "Alignment":
        line1_index = self.row_index(line1)
        line2_index = self.row_index(line2)
        index1, index2 = sorted((line1_index, line2_index))
        _, split_index = min((self.bond_strengths[i], i) for i in range(index1, index2))
        return self.alignments[split_index]

    def can_split(self, line1: TextLine, line2: TextLine) -> bool:
        if self.row_index(line1) == self.row_index(line2):
            return False
        alignment = self.alignment(line1, line2)
        return not (alignment.no_gap and alignment.left_aligned)

    def row_index(self, line: TextLine) -> int:
        return next(i for i, row in enumerate(self.rows) if line in row)

    def extra_info(self) -> list[str]:
        return [
            char_box.extra_info
            for line in self.lines
            for char_box in line.char_boxes
            if char_box.extra_info
        ]

    def __str__(self):
        return self.content()

    def __hash__(self):
        return id(self)


def compare_text_blocks(block1: TextBlock, block2: TextBlock):
    if block1.end.y - block2.font.height / 2 <= block2.start.y:
        return -1
    if block1.start.y >= block2.end.y - block2.font.height / 2:
        return 1
    if block1.start.x < block2.start.x:
        if block1.start.y - block1.font.height*1.5 <= block2.start.y:
            return -1
        if block1.end.y <= block2.end.y:
            return -1
        logger.warning(f"Ambiguous block order {block1.box} {block2.box} {block1.font.height}")
        return 1
    if block1.start.x > block2.start.x:
        if block1.start.y >= block2.start.y - block2.font.height*1.5:
            return 1
        if block1.end.y >= block2.end.y:
            return 1
        logger.warning(f"Ambiguous block order {block2.box} {block1.box} {block2.font.height}")
        return -1
    return 0


def sort_text_blocks(text_blocks: Iterable[TextBlock]) -> list[TextBlock]:
    return sorted(text_blocks, key=cmp_to_key(compare_text_blocks))


def mark_excluding_trailing_spaces(s: str, markers: str) -> str:
    trailing_spaces = re.search(r" *$", s).group()
    return f'{markers[0]}{s.rstrip()}{markers[1]}{trailing_spaces}'


@dataclass
class Alignment:
    left_aligned: bool
    char_aligned: bool
    no_gap: bool

    @property
    def strength(self):
        bond_strength = 0
        if self.left_aligned:
            bond_strength += 5
        elif self.char_aligned:
            bond_strength += 3
        if self.no_gap:
            bond_strength += 10
        return bond_strength


def get_text_blocks(text_lines: list[TextLine]) -> Iterable[TextBlock]:
    grouped_lines = group_text_lines(text_lines)
    while grouped_lines:
        new_block = [grouped_lines[0]]
        alignments = []
        font = grouped_lines[0][0].font
        new_lines: list[list[TextLine]] = []
        for text_line_group in grouped_lines[1:]:
            alignment = fit_to_block(text_line_group, new_block[-1], font)
            if alignment is not None:
                new_block.append(text_line_group)
                alignments.append(alignment)
            else:
                new_lines.append(text_line_group)
        grouped_lines = new_lines
        color = new_block[0][0].color
        yield TextBlock(new_block, alignments, color, font)


def fit_to_block(line_group: list[TextLine], previous_group: list[TextLine], font: Font) -> Alignment | None:
    if line_group[0].font.group != font.group:
        return None
    if line_group[0].color != previous_group[0].color:
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
    previous_right = previous_last_box.right
    previous_bottom = max(previous_first_box.bottom, previous_last_box.bottom)
    if get_interval_distance(
        (left, right),
        (previous_left, previous_right),
    ) != 0:
        return None
    previous_height = font.height
    previous_width = font.space_width
    common_part = min(right - previous_left, previous_right - left)
    if common_part < previous_width:
        return None
    if previous_bottom - 1 <= top <= previous_bottom + previous_height // 6:
        return Alignment(
            left_aligned=previous_left == left,
            char_aligned=(previous_left - left) % previous_width == 0 and font.is_mono,
            no_gap=top <= previous_bottom,
        )
    return None
