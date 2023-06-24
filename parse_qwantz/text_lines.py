import logging
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

logger = logging.getLogger()


@dataclass
class TextLine:
    char_boxes: list[CharBox]
    font: Font
    color: Color

    def __repr__(self):
        return f"TextLine({repr(self.start)}, {repr(self.content)}, {self.font.name})"

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
        x0, y0 = self.start
        x1, y1 = self.end
        return Box(Pixel(x0 - padding, y0 - padding), Pixel(x1 + padding, y1 + padding))

    def find_pixel(self) -> Pixel:
        return min(self.char_boxes[0].pixels)

    def __hash__(self):
        return id(self)


def try_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    x0, y0 = start
    if font.italic_offsets:
        max_x_offset = font.space_width - 3
    else:
        max_x_offset = 0
    max_y_offset = font.height - 1
    for x in range(x0 - max_x_offset, x0 + 1):
        for y in range(y0, y0 - max_y_offset - 1, -1):
            line = get_text_line(Pixel(x, y), image, font)
            if line:
                return line


def get_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
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
        if char_box is None and spaces:
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
                line, _pixels = result
                if (
                    min(line[0].x, line[1].x) < char_box.box.left
                    or min(line[0].y, line[1].y) < char_box.box.top
                    or max(line[0].x, line[1].x) > char_box.box.right
                    or max(line[0].y, line[1].y) > char_box.box.bottom
                ):
                    break
        if inline_offset_warning:
            logger.warning(inline_offset_warning)
        if char_box.char == ' ':
            spaces.append(
                CharBox.space(is_bold, is_italic, char_box.box)
            )
            exploded = all(char_box.char == ' ' for char_box in char_boxes[1::2])
            after_period = char_boxes[-1].char in '.,?!"'
            if not exploded and len(spaces) > 1 and not after_period:
                break
            if not exploded and len(spaces) > 2:
                break
            if len(spaces) > 3:
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
        and first_char not in '!?'
        and not (first_char == '-' and font.group == 'LC13')
    ):
        return
    if len(char_boxes) >= 2 and all(char_box.char in " \",.'‘’“”|-/·•" for char_box in char_boxes):
        if ''.join(char_box.char for char_box in char_boxes) != "...":
            return
    char_boxes = list(adjust_spaces(char_boxes))
    if len(char_boxes) >= 5 and all(char_box.char == ' ' for char_box in char_boxes[1::2]):
        char_boxes = char_boxes[0::2]
    if len(char_boxes) > 2 and char_boxes[-1].char == "'" and char_boxes[-2].char == " ":
        char_boxes = char_boxes[:-2]
    color = image.get_pixel(min(char_boxes[0].pixels))
    return TextLine(char_boxes, font, color)


def adjust_spaces(char_boxes: list[CharBox]) -> Iterable[CharBox]:
    for char_box, next_char_box in zip(char_boxes, chain(char_boxes[1:], [None])):
        if char_box.char == ' ' and char_box.box.right > next_char_box.box.left:
            new_box = Box(char_box.box.top_left, Pixel(next_char_box.box.left, char_box.box.bottom))
            if new_box.width > 2:
                yield char_box.with_box(new_box)
        else:
            yield char_box


def cleanup_text_lines(text_lines: list[TextLine], image: SimpleImage) -> list[TextLine]:
    grouped_lines = group_text_lines(sorted(text_lines, key=lambda l: l.start))
    return sorted(
        chain.from_iterable(_join_text_lines(group, image) for group in grouped_lines),
        key=lambda l: (l.start.y, l.start.x)
    )


def group_text_lines(
    text_lines: list[TextLine], same_font: bool = False, long_space: bool = False
) -> list[list[TextLine]]:
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
            if same_font and other_text_line.font.group != text_line.font.group:
                continue
            box = group[-1].box()
            other_box = other_text_line.box()
            if abs(box.top + text_line.font.base - (other_box.top + other_text_line.font.base)) <= 1:
                distance = other_box.left - box.right
                width = max(group[-1].font.space_width, other_text_line.font.space_width)
                max_distance = width * 3 if long_space else width * 2 + 1
                if -1 <= distance <= max_distance:
                    group.append(other_text_line)
                    used.add(other_text_line)
        grouped_text_lines.append(group)
    return grouped_text_lines


def _join_text_lines(text_lines: list[TextLine], image: SimpleImage) -> list[TextLine]:
    if len(text_lines) == 1:
        return text_lines
    for font in (line.font for line in text_lines):
        if font == text_lines[0].font:
            continue
        first_pixel = text_lines[0].find_pixel()
        if joined_text_line := try_text_line(first_pixel, image, font):
            joined_box = joined_text_line.box()
            for i, text_line in enumerate(text_lines[1:], start=1):
                if abs(joined_box.right - text_lines[i].box().right) < font.space_width // 2:
                    return [joined_text_line, *text_lines[i+1:]]
    return text_lines
