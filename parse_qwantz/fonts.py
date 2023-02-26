from dataclasses import dataclass
from importlib.resources import as_file, files
from itertools import islice, chain
from pathlib import Path
from typing import NamedTuple, ContextManager, Iterator, ForwardRef, Union

from PIL import Image

import parse_qwantz
from parse_qwantz.box import Box
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage

CHARS = """0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&'()*+,-./:;<=>?@[]^{|}‘’“”·•™é"""
FORBIDDEN_FIRST_CHARS = "%&)+/;=@]^|}”·™"

ACCEPT = -1

FONT_SIZES = [
    (13, 'Regular', 2, 1),
    (12, 'Condensed', 0, 0),
    (11, 'Small', 0, 0),
    (10, 'Petite', 0, 0),
    (9, 'Mini', 0, 0),
    (8, 'Tiny', 0, 0),
]


class CharBox(NamedTuple):
    char: str
    box: Box
    is_bold: bool
    is_italic: bool

    def pixels(self, italic_offsets: set[int]):
        if not italic_offsets:
            return [
                (x, y)
                for x in range(self.box.left, self.box.right)
                for y in range(self.box.top, self.box.bottom)
            ]
        else:
            pixels = []
            italic_offset = len(italic_offsets)
            for y in range(self.box.top, self.box.bottom):
                if y - self.box.top in italic_offsets:
                    italic_offset -= 1
                for x in range(self.box.left, self.box.right):
                    pixels.append((x + italic_offset, y))
            return pixels

    def with_box(self, box: Box):
        return CharBox(self.char, box, self.is_bold, self.is_italic)

    @classmethod
    def space(cls, is_bold: bool, is_italic: bool) -> "CharBox":
        return cls(char=' ', box=Box.dummy(), is_bold=is_bold, is_italic=is_italic)


@dataclass
class CharInfo:
    char: str
    left_padding: int
    right_padding: int


FSA_BACKREF = ForwardRef("FSA")

FSA = dict[int, Union[FSA_BACKREF, CharInfo]]


@dataclass
class Font:
    name: str
    width: int
    height: int
    automaton: FSA
    initial_padding: int
    final_padding: int
    is_bold: bool
    italic_offsets: set[int]
    group: str
    max_cut_bottom: int
    max_cut_top: int

    def get_char(
        self,
        pixel: Pixel,
        image: SimpleImage,
        is_first: bool = False,
    ) -> CharBox | None:
        if char_box := self._get_char_box_from_columns(pixel, self._get_columns(pixel, image), is_first):
            return char_box

        for cut_bottom in range(1, self.max_cut_bottom + 1):
            columns = self._get_columns(pixel, image, cut_bottom=cut_bottom)
            if char_box := self._get_char_box_from_columns(pixel, columns, is_first):
                box = char_box.box
                return char_box.with_box(Box(box.top_left, Pixel(box.right, box.bottom - cut_bottom)))

        for cut_top in range(1, self.max_cut_top + 1):
            columns = self._get_columns(pixel, image, cut_top=cut_top)
            if char_box := self._get_char_box_from_columns(pixel, columns, is_first):
                box = char_box.box
                return char_box.with_box(Box(Pixel(box.left, box.top + cut_top), box.bottom_right))

    def _get_char_box_from_columns(
        self, pixel: Pixel, columns: Iterator[tuple[int, int]], is_first: bool
    ) -> CharBox | None:
        is_italic = bool(self.italic_offsets)
        x = column = 0  # to satisfy linters; columns are never empty
        for x, column in islice(columns, self.initial_padding + 1):
            if column != 0:
                break
        else:
            for x, column in columns:
                if column != 0:
                    return CharBox(' ', Box(pixel, Pixel(x, pixel.y + self.height)), self.is_bold, is_italic)
        x0 = x
        state = self.automaton
        for x, column in chain([(x0, column)], columns):
            if column not in state:
                return
            state = state[column]
            if ACCEPT in state:
                break
        char_info: CharInfo = state[ACCEPT]
        if is_first and char_info.char in FORBIDDEN_FIRST_CHARS:
            return
        return CharBox(
            char_info.char,
            Box(
                Pixel(x0 - char_info.left_padding, pixel.y),
                Pixel(x + 1, pixel.y + self.height),
            ),
            self.is_bold,
            is_italic,
        )

    def _get_columns(
        self, pixel: Pixel,
        image: SimpleImage,
        cut_bottom: int = 0,
        cut_top: int = 0,
    ) -> Iterator[tuple[int, int]]:
        for x in range(pixel.x, min(image.width + self.final_padding, pixel.x + self.width * 3)):
            yield x, self._get_column(x, pixel.y, image, cut_bottom, cut_top)

    def _get_column(self, x: int, y: int, image: SimpleImage, cut_bottom: int, cut_top: int) -> int:
        return get_column(x, y, image, self.height, self.italic_offsets, cut_bottom, cut_top)

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Font(name={self.name}, width={self.width}, height={self.height})"

    @classmethod
    def from_file(
        cls,
        file_path_context_manager: ContextManager[Path],
        name: str,
        italic_offsets: set[int],
        is_bold: bool,
        group: str,
        max_cut_bottom: int,
        max_cut_top: int,
    ) -> "Font":
        with file_path_context_manager as file_path:
            image = SimpleImage.from_image(Image.open(file_path))
        input_width = image.width // len(CHARS)
        output_width = input_width + 1 if is_bold else input_width
        height = image.height
        automaton: FSA = {}
        accepting_states: list[CharInfo] = []
        for i, char in enumerate(CHARS):
            columns = get_input_columns(i, image, input_width, height, italic_offsets, is_bold)
            if maybe_char_info := update_automaton(char, columns, automaton, output_width):
                accepting_states.append(maybe_char_info)
            if height > 12:
                if char not in 'gq[]':
                    columns = get_input_columns(i, image, input_width, height, italic_offsets, is_bold, cut_bottom=1)
                    update_automaton(char, columns, automaton, output_width)
                if char not in 'fl':
                    columns = get_input_columns(i, image, input_width, height, italic_offsets, is_bold, cut_top=1)
                    update_automaton(char, columns, automaton, output_width)
        initial_padding = max(char_info.left_padding for char_info in accepting_states)
        final_padding = max(char_info.right_padding for char_info in accepting_states)
        return cls(
            name,
            output_width,
            height,
            automaton,
            initial_padding,
            final_padding,
            is_bold,
            italic_offsets,
            group,
            max_cut_bottom,
            max_cut_top,
        )


def get_input_columns(
    index: int,
    image: SimpleImage,
    width: int,
    height: int,
    italic_offsets: set[int],
    is_bold: bool,
    cut_bottom: int = 0,
    cut_top: int = 0,
):
    columns = [
        get_column(width * index + j, 0, image, height, italic_offsets, cut_bottom, cut_top)
        for j in range(width)
    ]
    if is_bold:
        columns = [column1 | column2 for column1, column2 in zip([0] + columns, columns + [0])]
    return columns


def get_column(
    x0: int, y0: int, image: SimpleImage, height: int, italic_offsets: set[int], cut_bottom: int, cut_top: int
) -> int:
    bitmask = 0
    italic_offset = len(italic_offsets)
    for y in range(y0, y0 + height):
        if y - y0 in italic_offsets:
            italic_offset -= 1
        bitmask <<= 1
        if (x0 + italic_offset, y) in image.pixels:
            bitmask += 1
    if cut_bottom:
        bitmask = bitmask & -(1 << cut_bottom)
    if cut_top:
        bitmask = bitmask & ((1 << height - cut_top) - 1)
    return bitmask


def update_automaton(
    char: str,
    columns: list[int],
    automaton: FSA,
    width: int,
) -> CharInfo | None:
    x = 0
    while columns[x] == 0:
        x += 1
    left_padding = x
    x = width - 1
    while columns[x] == 0:
        x -= 1
    right_padding = width - 1 - x
    state = automaton
    for column in columns[left_padding:]:
        state = state.setdefault(column, {})
    # “ and ” look the same as " in some sizes,
    # but we prefer O than 0 when they look the same
    if ACCEPT not in state or char == "O":
        state[ACCEPT] = CharInfo(char, left_padding, right_padding)
        return state[ACCEPT]


ALL_FONTS = [
    Font.from_file(
        file_path_context_manager=as_file(files(parse_qwantz).joinpath(f'img/regular{size}.png')),
        name=name,
        italic_offsets=set(),
        is_bold=is_bold,
        group=f'LC{size}',
        max_cut_bottom=max_cut_bottom,
        max_cut_top=max_cut_top,
    )
    for size, name, max_cut_bottom, max_cut_top in FONT_SIZES
    for is_bold in (False, True)
]

ALL_FONTS.append(
    Font.from_file(
        file_path_context_manager=as_file(files(parse_qwantz).joinpath(f'img/italic13.png')),
        name='Italic',
        italic_offsets={3, 5, 9, 11},
        is_bold=False,
        group='LC13',
        max_cut_bottom=0,
        max_cut_top=0,
    )
)
