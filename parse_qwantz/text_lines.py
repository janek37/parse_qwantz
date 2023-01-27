from functools import cached_property

from dataclasses import dataclass

from parse_qwantz.box import Box
from parse_qwantz.fonts import Font, CharBox
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage


@dataclass
class TextLine:
    char_boxes: list[CharBox]
    font: Font

    def __repr__(self):
        return f"TextLine({repr(self.start)}, {repr(self.content)}, {self.font.name})"

    @property
    def start(self) -> Pixel:
        return self.char_boxes[0].box.top_left

    @property
    def end(self) -> Pixel:
        return Pixel(self.x_end, self.y_end)

    @cached_property
    def content(self) -> str:
        content = ''.join(char_box.char for char_box in self.char_boxes)
        return content

    @cached_property
    def is_bold(self) -> bool:
        return all(char_box.is_bold for char_box in self.char_boxes)

    @property
    def contains_bold(self) -> bool:
        return any(char_box.is_bold for char_box in self.char_boxes if char_box.char != ' ')

    def box(self, padding: int = 0) -> Box:
        x, y = self.start
        return Box(Pixel(x - padding, y - padding), Pixel(self.x_end + padding, self.y_end + padding))

    @cached_property
    def x_end(self) -> int:
        return self.char_boxes[-1].box.right

    @cached_property
    def y_end(self) -> int:
        return max(y for _, (_, (_, y)), _ in self.char_boxes)

    def __hash__(self):
        return id(self)


def try_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    x0, y0 = start
    for x in range(x0, x0 - font.width + 1, -1):
        for y in range(y0, y0 - font.height + 1, -1):
            line = get_text_line(Pixel(x, y), image, font)
            if line:
                return line


def get_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    char_box = font.get_char(start, image=image, expect_space=False)
    if char_box is None or char_box.char == ' ':
        return None
    char_boxes = [char_box]
    spaces = []
    is_bold = char_box.is_bold
    x, y = start
    while True:
        x += char_box.box.width
        if x > image.width - font.width:
            break
        char_box = font.get_char(Pixel(x, y), image, expect_bold=is_bold)
        if char_box is None:
            if spaces:
                offsets = ((-2, 0), (-1, 0), (1, 0), (0, -1), (0, 1))
            else:
                offsets = ((-2, 0), (-1, 0), (1, 0))
            for offset in offsets:
                off_x, off_y = offset
                char_box = font.get_char(Pixel(x + off_x, y + off_y), image, expect_space=False)
                if char_box and char_box.char == ' ':
                    char_box = None
                if char_box is not None:
                    x += off_x
                    y += off_y
                    break
        if char_box is None:
            break
        # this is to avoid treating "i"/"j" dots as periods, but still allow lines starting with "..."
        if len(char_boxes) == 1 and char_boxes[0].char == '.' and char_box.char != '.':
            return None
        elif char_box.char == ' ':
            spaces.append(CharBox(' ', Box(Pixel(x, y), Pixel(x + font.width, y + font.height)), is_bold))
            exploded = all(char_box.char == ' ' for char_box in char_boxes[1::2])
            after_period = char_boxes[-1].char in '.?!"'
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
    if len(char_boxes) <= 2 and all(char_box.char in "\",.'`|-/\\" for char_box in char_boxes):
        return
    if len(char_boxes) > 5 and all(char_box.char == ' ' for char_box in char_boxes[1::2]):
        char_boxes = char_boxes[0::2]
    return TextLine(char_boxes, font)
