import string
from PIL import Image

SHAPE_FILE = 'img/printable.png'

REGULAR_HEIGHT = 13
REGULAR_WIDTH = 8

BOLD_HEIGHT = 13
BOLD_WIDTH = 9

WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 255)


def get_regular_shapes() -> dict[int, str]:
    image = Image.open(SHAPE_FILE)
    return {
        get_regular_bitmask(x=REGULAR_WIDTH*i, y=0, image=image): char
        for i, char in enumerate(string.printable.strip())
    }


def get_regular_bitmask(x: int, y: int, image: Image):
    return get_bitmask(x, y, image, REGULAR_WIDTH, REGULAR_HEIGHT)


def get_bitmask(x: int, y: int, image: Image, width: int, height: int) -> int:
    bitmask = 0
    x0, y0 = x, y
    for y in range(height):
        for x in range(width):
            bitmask <<= 1
            color = image.getpixel((x0 + x, y0 + y))
            if color != WHITE:
                bitmask += 1
    return bitmask


REGULAR_SHAPES = get_regular_shapes()

