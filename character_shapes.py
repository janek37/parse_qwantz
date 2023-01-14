import string
from dataclasses import dataclass

from PIL import Image

from pixels import Pixel, SimpleImage

PRINTABLE = string.printable.strip()

REGULAR_SHAPE_FILE = 'img/regular.png'


@dataclass
class Font:
    width: int
    height: int
    shapes: dict[int, str]

    def get_char(self, pixel: Pixel, image: SimpleImage) -> str | None:
        bitmask = self._get_bitmask(pixel, image)
        if bitmask == 0:
            return ' '
        return self.shapes.get(bitmask)

    def _get_bitmask(self, pixel: Pixel, image: SimpleImage) -> int:
        return get_bitmask(pixel, image, self.width, self.height)


def get_regular_shapes(file_path: str) -> tuple[int, int, dict[int, str]]:
    image = SimpleImage.from_image(Image.open(file_path))
    width = image.width // len(PRINTABLE)
    height = image.height
    return width, height, {
        get_bitmask((width * i, 0), image=image, width=width, height=height): char
        for i, char in enumerate(PRINTABLE)
    }


def get_bold_shapes(regular_font: Font) -> tuple[int, int, dict[int, str]]:
    return regular_font.width + 1, regular_font.height, {
        regular_shape_to_bold(shape, regular_font): char
        for shape, char in regular_font.shapes.items()
    }


def regular_shape_to_bold(shape: int, regular_font: Font) -> int:
    bold = 0
    mask = (1 << regular_font.width) - 1
    for level in range(regular_font.height):
        line = shape & mask
        bold_line = line | (line << 1)
        bold |= bold_line << (level * (regular_font.width + 1))
        shape >>= regular_font.width
    return bold


def get_bitmask(pixel: Pixel, image: SimpleImage, width: int, height: int) -> int:
    bitmask = 0
    x0, y0 = pixel
    for y in range(height):
        for x in range(width):
            bitmask <<= 1
            if (x0 + x, y0 + y) in image.pixels:
                bitmask += 1
    return bitmask


REGULAR_FONT = Font(*get_regular_shapes(REGULAR_SHAPE_FILE))
BOLD_FONT = Font(*get_bold_shapes(REGULAR_FONT))
