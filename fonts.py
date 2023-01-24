import string
from dataclasses import dataclass
from itertools import product
from typing import NamedTuple

from PIL import Image

from box import Box
from pixels import Pixel
from simple_image import SimpleImage

PRINTABLE = string.printable.strip()
FORBIDDEN_CHARS = '\\_`|~'

REGULAR13_SHAPE_FILE = 'img/regular13.png'
REGULAR12_SHAPE_FILE = 'img/regular12.png'
REGULAR11_SHAPE_FILE = 'img/regular11.png'
REGULAR9_SHAPE_FILE = 'img/regular9.png'
REGULAR8_SHAPE_FILE = 'img/regular8.png'


class CharBox(NamedTuple):
    char: str
    box: Box
    is_bold: bool


@dataclass
class Font:
    name: str
    width: int
    height: int
    shapes: dict[int, str]
    bold_shapes: dict[int, str]

    def get_char(self, pixel: Pixel, image: SimpleImage, expect_bold: bool = False) -> CharBox | None:
        if char_box := self.get_char_with_weight(pixel, image, is_bold=expect_bold):
            return char_box
        return self.get_char_with_weight(pixel, image, is_bold=not expect_bold)

    def get_char_with_weight(self, pixel: Pixel, image: SimpleImage, is_bold: bool) -> CharBox | None:
        width = self.width + 1 if is_bold else self.width
        bottom_right = Pixel(pixel.x + width, pixel.y + self.height)
        bitmask = self._get_bitmask(pixel, image, is_bold)
        if bitmask == 0:
            return CharBox(' ', Box(pixel, bottom_right), is_bold)
        if char := self._get_char_by_bitmask(bitmask, is_bold):
            return CharBox(char, Box(pixel, bottom_right), is_bold)
        for cut_bottom in range(1, 3):
            cut_bitmask = bitmask & -(1 << (width * cut_bottom))
            if cut_bitmask & -cut_bitmask > (1 << (width * (cut_bottom + 1))):
                if char := self._get_char_by_bitmask(cut_bitmask, is_bold):
                    right, bottom = bottom_right
                    return CharBox(char, Box(pixel, Pixel(right, bottom - cut_bottom)), is_bold)
        right, bottom = bottom_right
        for x, y in product(range(pixel.x, right), range(pixel.y, bottom)):
            if Pixel(x, y) in image.pixels:
                if x >= right - 2:
                    return CharBox(' ', Box(pixel, Pixel(x, bottom)), is_bold)
                break

    def _get_bitmask(self, pixel: Pixel, image: SimpleImage, is_bold: bool) -> int:
        width = self.width + 1 if is_bold else self.width
        return get_bitmask(pixel, image, width, self.height)

    def _get_char_by_bitmask(self, bitmask: int, is_bold: bool) -> str | None:
        shapes = self.bold_shapes if is_bold else self.shapes
        char = shapes.get(bitmask)
        if char and char not in FORBIDDEN_CHARS:
            return char

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Font(name={self.name}, width={self.width}, height={self.height})"

    @classmethod
    def from_file(
        cls, file_path: str, name: str, shifted_variants: dict[str, int] | None = None
    ) -> "Font":
        image = SimpleImage.from_image(Image.open(file_path))
        width = image.width // len(PRINTABLE)
        height = image.height
        shapes = {}
        for i, char in enumerate(PRINTABLE):
            bitmask = get_bitmask(Pixel(width * i, 0), image=image, width=width, height=height)
            shapes[bitmask] = char
            if shifted_variants and char in shifted_variants:
                shapes[get_shifted_variant(bitmask, width, height, shifted_variants[char])] = char
            cut_bitmask = bitmask & -(1 << width)
            if cut_bitmask != bitmask and char not in 'gq[]':
                shapes[cut_bitmask] = char
        return cls(name, width, height, shapes, get_bold_shapes(width, height, shapes))


def get_shifted_variant(shape: int, width: int, height: int, offset: int) -> int:
    shifted = 0
    mask = (1 << width) - 1
    for level in range(height):
        line = shape & mask
        shifted_line = line >> offset
        shifted |= shifted_line << (level * width)
        shape >>= width
    return shifted


def get_bold_shapes(width: int, height: int, shapes: dict[int, str]) -> dict[int, str]:
    return {
        regular_shape_to_bold(shape, width, height): char
        for shape, char in shapes.items()
    }


def regular_shape_to_bold(shape: int, width: int, height: int) -> int:
    bold = 0
    mask = (1 << width) - 1
    for level in range(height):
        line = shape & mask
        bold_line = line | (line << 1)
        bold |= bold_line << (level * (width + 1))
        shape >>= width
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


REGULAR_FONT = Font.from_file(REGULAR13_SHAPE_FILE, 'Regular', shifted_variants={',': 1, ':': 1, 'r': 1})
CONDENSED_FONT = Font.from_file(REGULAR12_SHAPE_FILE, 'Condensed')
SMALL_FONT = Font.from_file(REGULAR11_SHAPE_FILE, 'Small')
MINI_FONT = Font.from_file(REGULAR9_SHAPE_FILE, 'Mini')
TINY_FONT = Font.from_file(REGULAR8_SHAPE_FILE, 'Tiny')

ALL_FONTS = [REGULAR_FONT, SMALL_FONT, TINY_FONT, CONDENSED_FONT, MINI_FONT]
