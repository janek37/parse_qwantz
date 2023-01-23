import string
from dataclasses import dataclass
from typing import NamedTuple

from PIL import Image

from box import Box
from pixels import Pixel
from simple_image import SimpleImage

PRINTABLE = string.printable.strip()
FORBIDDEN_CHARS = '\\_`|'

REGULAR_SHAPE_FILE = 'img/regular.png'
REGULAR12_SHAPE_FILE = 'img/regular12.png'
REGULAR11_SHAPE_FILE = 'img/regular11.png'
REGULAR9_SHAPE_FILE = 'img/regular9.png'
REGULAR8_SHAPE_FILE = 'img/regular8.png'


class CharacterBox(NamedTuple):
    char: str
    box: Box


@dataclass
class Font:
    name: str
    width: int
    height: int
    shapes: dict[int, str]
    is_bold: bool = False

    def get_char(self, pixel: Pixel, image: SimpleImage) -> CharacterBox | None:
        bottom_right = Pixel(pixel.x + self.width, pixel.y + self.height)
        bitmask = self._get_bitmask(pixel, image)
        if bitmask == 0:
            return CharacterBox(' ', Box(pixel, bottom_right))
        if char := self._get_char_by_bitmask(bitmask):
            return CharacterBox(char, Box(pixel, bottom_right))
        for cut_bottom in range(1, 3):
            cut_bitmask = bitmask & -(1 << (self.width * cut_bottom))
            if cut_bitmask & -cut_bitmask > (1 << ((self.width + 1) * cut_bottom)):
                if char := self._get_char_by_bitmask(cut_bitmask):
                    right, bottom = bottom_right
                    return CharacterBox(char, Box(pixel, Pixel(right, bottom - cut_bottom)))

    def _get_bitmask(self, pixel: Pixel, image: SimpleImage) -> int:
        return get_bitmask(pixel, image, self.width, self.height)

    def _get_char_by_bitmask(self, bitmask: int) -> str | None:
        char = self.shapes.get(bitmask)
        if char and char not in FORBIDDEN_CHARS:
            return char

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
        bitmask = get_bitmask(Pixel(width * i, 0), image=image, width=width, height=height)
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


REGULAR_FONT = Font('Regular', *get_regular_shapes(REGULAR_SHAPE_FILE, shifted_variants={',': 1, ':': 1}))
BOLD_FONT = Font('Bold', *get_bold_shapes(REGULAR_FONT), True)
CONDENSED_FONT = Font('Condensed', *get_regular_shapes(REGULAR12_SHAPE_FILE))
SMALL_FONT = Font('Small', *get_regular_shapes(REGULAR11_SHAPE_FILE))
MINI_FONT = Font('Mini', *get_regular_shapes(REGULAR9_SHAPE_FILE))
TINY_FONT = Font('Tiny', *get_regular_shapes(REGULAR8_SHAPE_FILE))


ALL_FONTS = [REGULAR_FONT, BOLD_FONT, SMALL_FONT, TINY_FONT, CONDENSED_FONT, MINI_FONT]


FONT_GROUPS = {
    REGULAR_FONT.name: [REGULAR_FONT, BOLD_FONT],
    BOLD_FONT.name: [REGULAR_FONT, BOLD_FONT],
    SMALL_FONT.name: [SMALL_FONT],
    TINY_FONT.name: [TINY_FONT],
    CONDENSED_FONT.name: [CONDENSED_FONT],
    MINI_FONT.name: [MINI_FONT],
}
