import string
from dataclasses import dataclass

from PIL import Image

REGULAR_SHAPE_FILE = 'img/regular.png'

REGULAR_HEIGHT = 13
REGULAR_WIDTH = 8

BOLD_HEIGHT = 13
BOLD_WIDTH = 9

WHITE = ((255, 255, 255, 255), 255)
BLACK = ((0, 0, 0, 255), 0)


@dataclass
class Font:
    width: int
    height: int
    shapes: dict[int, str]

    def get_char(self, x: int, y: int, image: Image) -> str | None:
        bitmask = self.get_bitmask(x, y, image)
        if bitmask == 0:
            return ' '
        return self.shapes.get(bitmask)

    def get_bitmask(self, x: int, y: int, image: Image) -> int:
        return get_bitmask(x, y, image, self.width, self.height)


def get_regular_shapes() -> dict[int, str]:
    image = Image.open(REGULAR_SHAPE_FILE)
    return {
        get_bitmask(x=REGULAR_WIDTH * i, y=0, image=image, width=REGULAR_WIDTH, height=REGULAR_HEIGHT): char
        for i, char in enumerate(string.printable.strip())
    }


def get_bold_shapes() -> dict[int, str]:
    return {
        regular_shape_to_bold(shape): char
        for shape, char in REGULAR_FONT.shapes.items()
    }


def regular_shape_to_bold(shape: int) -> int:
    bold = 0
    mask = (1 << REGULAR_WIDTH) - 1
    for level in range(REGULAR_HEIGHT):
        line = shape & mask
        bold_line = line | (line << 1)
        bold |= bold_line << (level * BOLD_WIDTH)
        shape >>= REGULAR_WIDTH
    return bold


def get_bitmask(x: int, y: int, image: Image, width: int, height: int) -> int:
    bitmask = 0
    x0, y0 = x, y
    for y in range(height):
        for x in range(width):
            bitmask <<= 1
            color = image.getpixel((x0 + x, y0 + y))
            if color not in WHITE:
                bitmask += 1
    return bitmask


REGULAR_FONT = Font(REGULAR_WIDTH, REGULAR_HEIGHT, get_regular_shapes())
BOLD_FONT = Font(BOLD_WIDTH, BOLD_HEIGHT, get_bold_shapes())
