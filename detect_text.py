from functools import cached_property

from dataclasses import dataclass

from box import Box
from character_shapes import Font, CharacterBox
from pixels import Pixel
from simple_image import SimpleImage


@dataclass
class TextLine:
    character_boxes: list[CharacterBox]
    font: Font

    def __repr__(self):
        return f"TextLine({repr(self.start)}, {repr(self.content)}, {self.font.name})"

    @property
    def start(self) -> Pixel:
        return self.character_boxes[0].box.top_left

    @cached_property
    def content(self) -> str:
        return ''.join(char for char, box in self.character_boxes)

    def box(self, margin: int = 0) -> Box:
        x, y = self.start
        return Box(Pixel(x - margin, y - margin), Pixel(self.x_end + margin, self.y_end + margin))

    @cached_property
    def x_end(self) -> int:
        return self.character_boxes[-1].box.right

    @cached_property
    def y_end(self) -> int:
        return max(y for _, (_, (_, y)) in self.character_boxes)


def try_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    x0, y0 = start
    for x in range(x0, x0 - font.width + 1, -1):
        for y in range(y0, y0 - font.height + 1, -1):
            line = get_text_line(Pixel(x, y), image, font)
            if line:
                return line


def get_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    char_box = font.get_char(start, image=image)
    if char_box is None or char_box.char == ' ':
        return None
    character_boxes = [char_box]
    spaces = []
    x, y = start
    while True:
        x += font.width
        if x > image.width - font.width:
            break
        char_box = font.get_char(Pixel(x, y), image)
        if char_box is None:
            for offset in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                off_x, off_y = offset
                char_box = font.get_char(Pixel(x + off_x, y + off_y), image)
                if char_box is not None:
                    x += off_x
                    y += off_y
                    break
        if char_box is None:
            break
        elif char_box.char == ' ':
            spaces.append(CharacterBox(' ', Box(Pixel(x, y), Pixel(x + font.width, y + font.height))))
            if len(spaces) > 2:
                break
        else:
            if spaces:
                character_boxes.extend(spaces)
                spaces = []
            character_boxes.append(char_box)
    if len(character_boxes) <= 2 and all(char_box.char in ",.'`|-/\\" for char_box in character_boxes):
        return
    return TextLine(character_boxes, font)
