import logging
from functools import cached_property

from dataclasses import dataclass
from itertools import chain

from parse_qwantz.box import Box
from parse_qwantz.fonts import Font, CharBox
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage

logger = logging.getLogger()


@dataclass
class TextLine:
    char_boxes: list[CharBox]
    font: Font

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

    def find_pixel(self, image) -> Pixel:
        return image.find_pixel(self.char_boxes[0].pixels(self.font.italic_offsets))

    def __hash__(self):
        return id(self)


def try_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    x0, y0 = start
    max_x_offset = font.width - 3
    max_y_offset = font.height - 1
    for x in range(x0, x0 - max_x_offset - 1, -1):
        for y in range(y0, y0 - max_y_offset - 1, -1):
            line = get_text_line(Pixel(x, y), image, font)
            if line:
                return line


def get_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    char_box = font.get_char(start, image=image, expect_space=False, is_first=True)
    if char_box is None or char_box.char == ' ':
        return None
    char_boxes = [char_box]
    spaces = []
    short_space = False
    is_bold = char_box.is_bold
    is_italic = char_box.is_italic
    x, y = start
    while True:
        x += char_box.box.width
        if x > image.width - font.width:
            break
        allow_short_space = not spaces and char_boxes[-1].char == '.'
        char_box = font.get_char(Pixel(x, y), image, expect_bold=is_bold, allow_short_space=allow_short_space)
        if char_box is None:
            if spaces:
                offsets = ((-2, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
            else:
                offsets = ((-1, 0), (1, 0))
            for offset in offsets:
                off_x, off_y = offset
                char_box = font.get_char(Pixel(x + off_x, y + off_y), image, expect_space=False)
                if char_box and char_box.char == ' ':
                    char_box = None
                if char_box is not None:
                    content_so_far = ''.join(char_box.char for char_box in char_boxes)
                    if off_x == -2 or off_y != 0:
                        logger.warning(
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
        if len(char_boxes) == 1 and char_boxes[0].char in "'‘’“\"" and not char_box.char.isalpha():
            return None
        elif char_box.char == ' ':
            if char_box.box.width < font.width:
                short_space = True
            spaces.append(CharBox(' ', Box(Pixel(x, y), Pixel(x + font.width, y + font.height)), is_bold, is_italic))
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
                if short_space:
                    logger.warning(f'Short space after {"".join(cb.char for cb in char_boxes)}: {char_box.box.width}')
                    short_space = False
            char_boxes.append(char_box)
            is_bold = char_box.is_bold
            is_italic = char_box.is_italic
    if len(char_boxes) <= 2 and all(char_box.char in "\",.'‘’“”|-/·•" for char_box in char_boxes):
        return
    if len(char_boxes) >= 5 and all(char_box.char == ' ' for char_box in char_boxes[1::2]):
        char_boxes = char_boxes[0::2]
    return TextLine(char_boxes, font)


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
            if abs(box.top - other_box.top) <= 1 or abs(box.bottom - other_box.bottom) <= 1:
                distance = other_box.left - box.right
                width = max(group[-1].font.width, other_text_line.font.width)
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
        first_pixel = text_lines[0].find_pixel(image)
        if joined_text_line := try_text_line(first_pixel, image, font):
            joined_box = joined_text_line.box()
            if abs(joined_box.right - text_lines[-1].box().right) < font.width // 2:
                return [joined_text_line]
    return text_lines
