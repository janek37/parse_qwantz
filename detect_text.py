from typing import NamedTuple

from character_shapes import Font
from pixels import Pixel, SimpleImage


class TextLine(NamedTuple):
    start: Pixel
    content: str
    font: Font

    def box(self) -> tuple[Pixel, Pixel]:
        x, y = self.start
        return self.start, (self.x_end(), y + self.font.height)

    def x_end(self):
        return self.start[0] + self.font.width * len(self.content)


def try_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    x0, y0 = start
    for x in range(x0, x0 - font.width + 1, -1):
        for y in range(y0, y0 - font.height + 1, -1):
            line = get_text_line((x, y), image, font)
            if line:
                return line


def get_text_line(start: Pixel, image: SimpleImage, font: Font) -> TextLine | None:
    text = font.get_char(start, image=image)
    if text in (' ', None):
        return None
    spaces = 0
    x, y = start
    while True:
        x += font.width
        if x > image.width - font.width:
            break
        char = font.get_char((x, y), image)
        if char == ' ':
            spaces += 1
            if spaces > 2:
                break
            if spaces == 2:
                last_char = text[-1]
                if last_char == '"':
                    if len(text) < 1:
                        break
                    last_char = text[-2]
                if last_char not in '.!?':
                    break
        elif char is not None:
            if spaces > 0:
                text += ' ' * spaces
                spaces = 0
            text += char
        else:
            break
    return TextLine(start, text, font)
