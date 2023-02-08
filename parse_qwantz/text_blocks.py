import logging
import re
from itertools import chain, groupby
from typing import Iterable, NamedTuple

from parse_qwantz.box import Box, get_interval_distance
from parse_qwantz.fonts import Font, CharBox
from parse_qwantz.colors import Color
from parse_qwantz.hyphens import disambiguate_hyphen
from parse_qwantz.text_lines import TextLine, try_text_line
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage

logger = logging.getLogger()


class TextBlock(NamedTuple):
    lines: list[TextLine]
    bond_strengths: list[int]
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
        right = max(line.end.x for line in self.lines)
        return Box(Pixel(left, top), Pixel(right, bottom))

    def content(self, mark_bold=True, include_font_name=False):
        char_boxes = []
        for line in self.lines:
            if char_boxes:
                if char_boxes[-1].char != '-' or char_boxes[-2].char in ' -':
                    char_boxes.append(CharBox.space(is_bold=char_boxes[-1].is_bold))
                else:
                    last_words = ''
                    for char_box in char_boxes[-2::-1]:
                        if char_box.char in '.,!?" ':
                            break
                        last_words = char_box.char + last_words
                    next_words = re.match(r'[^.,!?" ]*', line.content).group()
                    last_word = last_words.rsplit('-', 1)[-1]
                    next_word = next_words.split('-', 1)[0]
                    if not disambiguate_hyphen(last_word, next_word):
                        char_boxes.pop()
                    else:
                        last_words += '-'
                    logger.info(f"Line ending with hyphen ({last_words}/{next_words})")
            char_boxes.extend(line.char_boxes)

        grouped_char_boxes = groupby(char_boxes, key=lambda cb: cb.is_bold and mark_bold)
        text_and_weight = (
            (''.join(char_box.char for char_box in group), is_bold)
            for is_bold, group in grouped_char_boxes
        )
        content = ''.join(
            make_bold_excluding_trailing_spaces(content) if is_bold else content
            for content, is_bold in text_and_weight
        )
        content = content.replace('  ', ' ')
        if self.font.italic_offsets:
            content = f'_{content}_'
        if include_font_name and self.font.name not in ('Regular', 'Italic'):
            content = f"({self.font.name.lower()}) {content}"
        return content

    def split(self, line1: TextLine, line2: TextLine) -> tuple["TextBlock", "TextBlock"]:
        line1_index = self.lines.index(line1)
        line2_index = self.lines.index(line2)
        index1, index2 = sorted((line1_index, line2_index))
        _, split_index = min((self.bond_strengths[i], i) for i in range(index1, index2))
        block1 = TextBlock(self.lines[:split_index+1], self.bond_strengths[:split_index], self.color, self.font)
        block2 = TextBlock(self.lines[split_index+1:], self.bond_strengths[split_index+1:], self.color, self.font)
        if line1_index < line2_index:
            return block1, block2
        else:
            return block2, block1

    def __str__(self):
        return self.content()

    def __hash__(self):
        return id(self)


def make_bold_excluding_trailing_spaces(s: str) -> str:
    trailing_spaces = re.search(r" *$", s).group()
    return f'**{s.rstrip()}**{trailing_spaces}'


def get_text_blocks(text_lines: list[TextLine], image: SimpleImage) -> Iterable[TextBlock]:
    grouped_lines = group_text_lines(text_lines)
    text_lines = sorted(
        chain.from_iterable(join_text_lines(group, image) for group in grouped_lines),
        key=lambda l: (l.start.y, l.start.x)
    )
    while text_lines:
        new_block = [text_lines[0]]
        bond_strengths = []
        font = text_lines[0].font
        new_lines: list[TextLine] = []
        for text_line in text_lines[1:]:
            append = False
            bond_strength = 0
            if text_line.font == font:
                text_box = text_line.box()
                previous_line = new_block[-1]
                bold_mismatch = previous_line.is_bold and not text_line.contains_bold
                if not bold_mismatch:
                    previous_box = previous_line.box()
                    intervals_intersect = get_interval_distance(
                        (text_box.left, text_box.right),
                        (previous_box.left, previous_box.right),
                    ) == 0
                    ceiling = previous_box.bottom
                    previous_height = previous_line.font.height
                    previous_width = previous_line.font.width
                    if ceiling - 1 <= text_box.top <= ceiling + previous_height // 6 and intervals_intersect:
                        if previous_box.left == text_box.left:
                            bond_strength += 5
                        elif (previous_box.left - text_box.left) % previous_width == 0:
                            bond_strength += 3
                        if text_box.top <= ceiling:
                            bond_strength += 10
                        if text_box.top >= ceiling + previous_height:
                            bond_strength -= 10
                        append = True
            if append:
                new_block.append(text_line)
                bond_strengths.append(bond_strength)
            else:
                new_lines.append(text_line)
        text_lines = new_lines
        found_pixel = new_block[0].find_pixel(image)
        color = image.pixels[found_pixel] if found_pixel else Color.WHITE
        yield TextBlock(new_block, bond_strengths, color, font)


def group_text_lines(text_lines: list[TextLine]) -> list[list[TextLine]]:
    grouped_text_lines = []
    used: set[TextLine] = set()
    for text_line in text_lines:
        if text_line in used:
            continue
        used.add(text_line)
        group = [text_line]
        box = text_line.box()
        for other_text_line in text_lines:
            if other_text_line in used:
                continue
            other_box = other_text_line.box()
            if abs(box.top - other_box.top) <= 1 or abs(box.bottom - other_box.bottom) <= 1:
                distance = other_box.left - box.right
                if -1 <= distance <= max(group[-1].font.width, other_text_line.font.width) * 2 + 1:
                    group.append(other_text_line)
                    used.add(other_text_line)
        grouped_text_lines.append(group)
    return grouped_text_lines


def join_text_lines(text_lines: list[TextLine], image: SimpleImage) -> list[TextLine]:
    if len(text_lines) == 1:
        return text_lines
    for font in (line.font for line in text_lines):
        if font == text_lines[0].font:
            continue
        first_pixel = text_lines[0].find_pixel(image)
        if joined_text_line := try_text_line(first_pixel, image, font):
            joined_box = joined_text_line.box()
            if abs(joined_box.right - text_lines[-1].box().right) < font.width // 2:
                return [joined_text_line]
    return text_lines
