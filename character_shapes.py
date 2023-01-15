import string
from dataclasses import dataclass

from PIL import Image

from pixels import Pixel, SimpleImage

PRINTABLE = string.printable.strip()

REGULAR_SHAPE_FILE = 'img/regular.png'
REGULAR11_SHAPE_FILE = 'img/regular11.png'


@dataclass
class Font:
    name: str
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

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Font(name={self.name}, width={self.width}, height={self.height})"


def get_regular_shapes(
    file_path: str, shifted_variants: dict[str, int] | None = None
) -> tuple[int, int, dict[int, str]]:
    image = SimpleImage.from_image(Image.open(file_path))
    width = image.width // len(PRINTABLE)
    height = image.height
    shapes = {}
    for i, char in enumerate(PRINTABLE):
        bitmask = get_bitmask((width * i, 0), image=image, width=width, height=height)
        shapes[bitmask] = char
        if shifted_variants and char in shifted_variants:
            shapes[get_shifted_variant(bitmask, width, height, shifted_variants[char])] = char
    return width, height, shapes


def get_shifted_variant(shape: int, width: int, height: int, offset: int) -> int:
    shifted = 0
    mask = (1 << width) - 1
    for level in range(height):
        line = shape & mask
        shifted_line = line >> offset
        shifted |= shifted_line << (level * width)
        shape >>= width
    return shifted


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


REGULAR_FONT = Font('Regular', *get_regular_shapes(REGULAR_SHAPE_FILE, shifted_variants={',': 1}))
BOLD_FONT = Font('Bold', *get_bold_shapes(REGULAR_FONT))
REGULAR11_FONT = Font('Small', *get_regular_shapes(REGULAR11_SHAPE_FILE))

ALL_FONTS = [REGULAR_FONT, BOLD_FONT, REGULAR11_FONT]
