import itertools
from dataclasses import dataclass
from importlib.resources import as_file, files
from itertools import islice, chain
from pathlib import Path
from typing import NamedTuple, ContextManager, Iterator

from PIL import Image

import parse_qwantz
from parse_qwantz.box import Box
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage

CHARS = """0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!"#$%&'()*+,-./:;<=>?@[]^{|}‘’“”·•™é"""
FORBIDDEN_FIRST_CHARS = "%&)+/;=@]^|}”·™"

FONT_SIZES = [(13, 'Regular'), (12, 'Condensed'), (11, 'Small'), (10, 'Petite'), (9, 'Mini'), (8, 'Tiny')]


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


@dataclass
class Font:
    name: str
    width: int
    height: int
    automaton: dict[tuple[int, int], int]
    accepting_states: dict[int, CharInfo]
    initial_padding: int
    final_padding: int
    is_bold: bool
    italic_offsets: set[int]
    group: str

    def get_char(
        self,
        pixel: Pixel,
        image: SimpleImage,
        is_first: bool = False,
    ) -> CharBox | None:
        if char_box := self._get_char_box_from_columns(pixel, self._get_columns(pixel, image), is_first):
            return char_box

        for cut_bottom in range(1, 3):
            columns = self._get_columns(pixel, image, cut_bottom=cut_bottom)
            if char_box := self._get_char_box_from_columns(pixel, columns, is_first):
                box = char_box.box
                return char_box.with_box(Box(box.top_left, Pixel(box.right, box.bottom - cut_bottom)))

        for cut_top in range(1, 2):
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
        state = 0
        for x, column in chain([(x0, column)], columns):
            if (state, column) not in self.automaton:
                return
            state = self.automaton[(state, column)]
            if state in self.accepting_states:
                break
        char_info = self.accepting_states[state]
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
    ) -> "Font":
        with file_path_context_manager as file_path:
            image = SimpleImage.from_image(Image.open(file_path))
        input_width = image.width // len(CHARS)
        output_width = input_width + 1 if is_bold else input_width
        height = image.height
        automaton: dict[tuple[int, int], int] = {}
        accepting_states: dict[int, CharInfo] = {}
        state_counter = itertools.count(1)
        for i, char in enumerate(CHARS):
            columns = get_input_columns(i, image, input_width, height, italic_offsets, is_bold)
            update_automaton(char, columns, automaton, accepting_states, output_width, state_counter)
            if height > 12:
                if char not in 'gq[]':
                    columns = get_input_columns(i, image, input_width, height, italic_offsets, is_bold, cut_bottom=1)
                    update_automaton(char, columns, automaton, accepting_states, output_width, state_counter)
                if char not in 'fl':
                    columns = get_input_columns(i, image, input_width, height, italic_offsets, is_bold, cut_top=1)
                    update_automaton(char, columns, automaton, accepting_states, output_width, state_counter)
        initial_padding = max(char_info.left_padding for char_info in accepting_states.values())
        final_padding = max(char_info.right_padding for char_info in accepting_states.values())
        return cls(
            name,
            output_width,
            height,
            automaton,
            accepting_states,
            initial_padding,
            final_padding,
            is_bold,
            italic_offsets,
            group
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
    automaton: dict[tuple[int, int], int],
    accepting_states: dict[int, CharInfo],
    width: int,
    state_counter: Iterator[int],
) -> None:
    x = 0
    while columns[x] == 0:
        x += 1
    left_padding = x
    x = width - 1
    while columns[x] == 0:
        x -= 1
    right_padding = width - 1 - x
    state = 0
    for column in columns[left_padding:]:
        if (state, column) not in automaton:
            automaton[(state, column)] = next(state_counter)
        state = automaton[(state, column)]
    # “ and ” look the same as " in some sizes,
    # but we prefer O than 0 when they look the same
    if state not in accepting_states or char == "O":
        accepting_states[state] = CharInfo(char, left_padding, right_padding)


ALL_FONTS = [
    Font.from_file(
        file_path_context_manager=as_file(files(parse_qwantz).joinpath(f'img/regular{size}.png')),
        name=name,
        italic_offsets=set(),
        is_bold=is_bold,
        group=f'LC{size}',
    )
    for size, name in FONT_SIZES
    for is_bold in (False, True)
]

ALL_FONTS.append(
    Font.from_file(
        file_path_context_manager=as_file(files(parse_qwantz).joinpath(f'img/italic13.png')),
        name='Italic',
        italic_offsets={3, 5, 9, 11},
        is_bold=False,
        group='LC13',
    )
)
