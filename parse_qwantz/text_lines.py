from functools import cached_property

from dataclasses import dataclass
from itertools import chain
from typing import Iterable

from parse_qwantz.box import Box
from parse_qwantz.colors import Color
from parse_qwantz.fonts import Font, CharBox
from parse_qwantz.lines import get_line
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage


GREEK_ALPHABET = "αάβγδεέζηήθιίκλμνξοόπρσςτυύφχψωώ"
LATIN_TO_GREEK = {
    "v": "ν",
    "o": "ο",
    "ó": "ό",
}


@dataclass(frozen=True, eq=True)
class TextLine:
    char_boxes: list[CharBox]
    font: Font
    color: Color

    def __repr__(self):
        return f"TextLine({repr(self.content)}, {self.font.name})"

    def __str__(self):
        return self.content

    @cached_property
    def start(self) -> Pixel:
        return self.char_boxes[0].box.top_left

    @cached_property
    def end(self) -> Pixel:
        return Pixel(
            x=self.char_boxes[-1].box.right + len(self.font.italic_offsets),
            y=max(char_box.box.bottom for char_box in self.char_boxes)
        )

    @cached_property
    def content(self) -> str:
        content = ''.join(char_box.char for char_box in self.char_boxes)
        return content

    @cached_property
    def is_bold(self) -> bool:
        return all(char_box.is_bold for char_box in self.char_boxes)

    @cached_property
    def is_italic(self) -> bool:
        return bool(self.font.italic_offsets)

    @property
    def contains_bold(self) -> bool:
        return any(char_box.is_bold for char_box in self.char_boxes if char_box.char != ' ')

    def box(self, padding: int = 0) -> Box:
        return Box(self.start, self.end).with_margin(padding, padding)

    def base_box(self, padding: int = 0) -> Box:
        _, y0 = self.start
        x1, _ = self.end
        y1 = y0 + self.font.base
        return Box(self.start, Pixel(x1, y1)).with_margin(padding, padding)

    def find_pixel(self) -> Pixel:
        return min(self.char_boxes[0].pixels)

    def __hash__(self):
        return id(self)


def try_text_line(start: Pixel, image: SimpleImage, font: Font) -> tuple[TextLine, list[str]] | None:
    x0, y0 = start
    if font.italic_offsets:
        max_x_offset = font.space_width - 3
    else:
        max_x_offset = 0
    max_y_offset = font.height - 1
    for x in range(x0 - max_x_offset, x0 + 1):
        for y in range(y0, y0 - max_y_offset - 1, -1):
            if result := get_text_line(Pixel(x, y), image, font):
                return result


def get_text_line(start: Pixel, image: SimpleImage, font: Font) -> tuple[TextLine, list[str]] | None:
    warnings = []
    char_box, complement = font.get_char(start, image=image, is_first=True)
    if char_box is None or char_box.char == ' ':
        return None
    char_boxes = [char_box]
    spaces = []
    is_bold = char_box.is_bold
    is_italic = char_box.is_italic
    x, y = start
    while True:
        x = char_box.box.right
        if x >= image.width:
            break
        char_box, complement = font.get_char(Pixel(x, y), image, first_column=complement)
        inline_offset_warning = None
        if char_box is None and not (len(char_boxes) == 1 and char_boxes[0].char == "'"):
            for offset in ((0, -1), (0, 1)):
                off_x, off_y = offset
                char_box, complement = font.get_char(Pixel(x + off_x, y + off_y), image)
                if char_box and char_box.char == ' ':
                    char_box = None
                if char_box is not None and char_box.char not in "_'":
                    content_so_far = ''.join(char_box.char for char_box in char_boxes)
                    inline_offset_warning = (
                        f"Inline offset after {content_so_far + ' '*len(spaces)!r},"
                        f" before {char_box.char!r}: {(off_x, off_y)}"
                    )
                    x += off_x
                    y += off_y
                    break
        if char_box is None:
            break
        # this is to avoid treating "i"/"j" dots as periods, but still allow lines starting with "..."
        if len(char_boxes) == 1 and char_boxes[0].char == '.' and char_box.char != '.':
            return None
        if char_box.char in "'|-":
            any_pixel = next(iter(char_box.pixels))
            result = get_line(any_pixel, image)
            if result:
                line, _pixels, _width = result
                if (
                    min(line[0].x, line[1].x) < char_box.box.left
                    or min(line[0].y, line[1].y) < char_box.box.top
                    or max(line[0].x, line[1].x) > char_box.box.right
                    or max(line[0].y, line[1].y) > char_box.box.bottom
                ):
                    break
        if inline_offset_warning:
            warnings.append(inline_offset_warning)
        if char_boxes:
            previous_char = char_boxes[-1].char
            if previous_char in GREEK_ALPHABET and char_box.char in LATIN_TO_GREEK:
                char_box = char_box.with_char(LATIN_TO_GREEK[char_box.char])
            elif previous_char in LATIN_TO_GREEK and char_box.char in GREEK_ALPHABET:
                char_boxes[-1] = char_boxes[-1].with_char(LATIN_TO_GREEK[previous_char])
        if char_box.char == ' ':
            if len(char_boxes) == 1 and char_boxes[0].char == "'":
                return
            spaces.append(
                CharBox.space(is_bold, is_italic, char_box.box)
            )
            if len(spaces) > 2:
                break
        else:
            if spaces:
                char_boxes.extend(spaces)
                spaces = []
            char_boxes.append(char_box)
            is_bold = char_box.is_bold
            is_italic = char_box.is_italic
    first_char = char_boxes[0].char
    if (
        len(char_boxes) == 1 and not first_char.isalnum()
        and first_char not in '!?$'
        and not (first_char == '-' and font.group == 'LC13')
        and not (first_char == '/' and font.name == "Regular" and not is_bold and not is_italic)
    ):
        return
    if len(char_boxes) >= 2 and all(char_box.char in " \",.'‘’“”|-/·•" for char_box in char_boxes):
        if ''.join(char_box.char for char_box in char_boxes) != "...":
            return
    char_boxes = list(adjust_spaces(char_boxes))
    if len(char_boxes) > 2 and char_boxes[-1].char == "'" and char_boxes[-2].char == " ":
        char_boxes = char_boxes[:-2]
    color = image.get_pixel(min(char_boxes[0].pixels))
    return TextLine(char_boxes, font, color), warnings


def adjust_spaces(char_boxes: list[CharBox]) -> Iterable[CharBox]:
    for char_box, next_char_box in zip(char_boxes, chain(char_boxes[1:], [None])):
        if char_box.char == ' ' and char_box.box.right > next_char_box.box.left:
            new_box = Box(char_box.box.top_left, Pixel(next_char_box.box.left, char_box.box.bottom))
            if new_box.width > 2:
                yield char_box.with_box(new_box)
        else:
            yield char_box


def cleanup_text_lines(text_lines: list[TextLine]) -> list[TextLine]:
    return sorted(
        text_lines,
        key=lambda l: (l.start.y, l.start.x)
    )


def group_text_lines(text_lines: list[TextLine]) -> list[list[TextLine]]:
    grouped_text_lines = []
    used: set[TextLine] = set()
    for text_line in text_lines:
        if text_line in used:
            continue
        used.add(text_line)
        group = [text_line]
        for other_text_line in text_lines:
            if other_text_line in used:
                continue
            if other_text_line.font.group != text_line.font.group:
                continue
            box = group[-1].base_box()
            other_box = other_text_line.base_box()
            vertical_offset = abs(box.bottom - other_box.bottom)
            same_font = other_text_line.font == text_line.font
            if (vertical_offset <= 1 and same_font) or vertical_offset == 0:
                distance = other_box.left - box.right
                width = max(group[-1].font.space_width, other_text_line.font.space_width)
                max_distance = width * 3
                if -1 <= distance <= max_distance:
                    group.append(other_text_line)
                    used.add(other_text_line)
        grouped_text_lines.append(group)
    return grouped_text_lines
