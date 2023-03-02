import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib.resources import as_file, files
from itertools import islice, chain
from pathlib import Path
from typing import NamedTuple, ContextManager, Iterator, ForwardRef, Union, Any

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
    pixels: set[Pixel]

    def with_box(self, box: Box):
        return CharBox(self.char, box, self.is_bold, self.is_italic, self.pixels)

    @classmethod
    def space(cls, is_bold: bool, is_italic: bool) -> "CharBox":
        return cls(char=' ', box=Box.dummy(), is_bold=is_bold, is_italic=is_italic, pixels=set())


@dataclass
class CharInfo:
    char: str
    left_padding: int
    right_padding: int


FSA_BACKREF = ForwardRef("FSA")

FSA = dict[int, Union[FSA_BACKREF, CharInfo]]


@dataclass
class Font(ABC):
    name: str
    space_width: int
    height: int
    automaton: FSA
    initial_padding: int
    final_padding: int
    is_bold: bool
    italic_offsets: set[int]
    group: str
    max_cut_bottom: int
    max_cut_top: int
    is_mono: bool = True

    def get_char(
        self,
        pixel: Pixel,
        image: SimpleImage,
        is_first: bool = False,
        first_column: int | None = None,
    ) -> tuple[CharBox | None, int | None]:
        char_box, complement = self._get_char_box_from_columns(
            pixel, self._get_columns(pixel, image), is_first, first_column
        )
        if char_box:
            return char_box, complement

        for cut_bottom in range(1, self.max_cut_bottom + 1):
            columns = self._get_columns(pixel, image, cut_bottom=cut_bottom)
            char_box, complement = self._get_char_box_from_columns(pixel, columns, is_first, first_column)
            if char_box:
                return char_box, complement

        for cut_top in range(1, self.max_cut_top + 1):
            columns = self._get_columns(pixel, image, cut_top=cut_top)
            char_box, complement = self._get_char_box_from_columns(pixel, columns, is_first, first_column)
            if char_box:
                return char_box, complement
        return None, None

    def _get_char_box_from_columns(
        self, pixel: Pixel, columns: Iterator[tuple[int, int]], is_first: bool, first_column: int | None
    ) -> tuple[CharBox | None, int | None]:
        is_italic = bool(self.italic_offsets)
        if first_column:
            x0 = pixel.x - 1
            column = first_column
        else:
            x = column = 0  # to satisfy linters; columns are never empty
            for x, column in islice(columns, self.initial_padding + 1):
                if column != 0:
                    break
            else:
                for x, column in columns:
                    if column != 0:
                        char_box = CharBox(
                            ' ',
                            Box(pixel, Pixel(x, pixel.y + self.height)),
                            self.is_bold,
                            is_italic,
                            set(),
                        )
                        return char_box, None
            x0 = x
        state = self.automaton
        accepted = None
        char_columns = []
        for x, column in chain([(x0, column)], columns):
            if column not in state:
                if not self.is_mono and len(state) == 1:
                    actual_column, next_state = next(iter(state.items()))
                    if actual_column != -1 and ACCEPT in next_state and column | actual_column == column:
                        complement = column & ~actual_column
                        if complement in self.automaton:
                            char_columns.append(actual_column)
                            accepted = (x, next_state[ACCEPT], complement, char_columns)
                if accepted:
                    break
                return None, None
            state = state[column]
            char_columns.append(column)
            if ACCEPT in state:
                accepted = (x, state[ACCEPT], None, list(char_columns))
        else:
            return None, None
        x, char_info, complement, char_columns = accepted
        if is_first and char_info.char in FORBIDDEN_FIRST_CHARS:
            return None, None
        pixels = get_pixels_from_columns(char_columns, self.height, x0, pixel.y, self.italic_offsets)
        return CharBox(
            char_info.char,
            Box(
                Pixel(x0 - char_info.left_padding, pixel.y),
                Pixel(x + 1, pixel.y + self.height),
            ),
            self.is_bold,
            is_italic,
            pixels,
        ), complement

    def _get_columns(
        self, pixel: Pixel,
        image: SimpleImage,
        cut_bottom: int = 0,
        cut_top: int = 0,
    ) -> Iterator[tuple[int, int]]:
        max_x = image.width + self.final_padding
        if self.is_mono:
            max_x = min(max_x, pixel.x + self.space_width * 3)
        for x in range(pixel.x, max_x):
            yield x, self._get_column(x, pixel.y, image, cut_bottom, cut_top)

    def _get_column(self, x: int, y: int, image: SimpleImage, cut_bottom: int, cut_top: int) -> int:
        return get_column(x, y, image, self.height, self.italic_offsets, cut_bottom, cut_top)

    def __str__(self):
        return self.name

    def __repr__(self):
        return (
            f"Font(name={self.name}, height={self.height}, "
            f"is_bold={self.is_bold}, is_italic={bool(self.italic_offsets)})"
        )

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
        **kwargs: Any,
    ) -> "Font":
        with file_path_context_manager as file_path:
            image = SimpleImage.from_image(Image.open(file_path))
        height = image.height
        automaton: FSA = {}
        accepting_states: list[CharInfo] = []
        for i, (char, columns) in enumerate(zip(CHARS, cls.get_input_columns(image, italic_offsets, is_bold))):
            if maybe_char_info := update_automaton(char, columns, automaton):
                accepting_states.append(maybe_char_info)
            if height > 12:
                if char not in 'gq[]':
                    cut_columns = [cut_column(c, height, cut_bottom=1) for c in columns]
                    update_automaton(char, cut_columns, automaton)
                if char not in 'fl':
                    cut_columns = [cut_column(c, height, cut_top=1) for c in columns]
                    update_automaton(char, cut_columns, automaton)
        initial_padding = max(char_info.left_padding for char_info in accepting_states)
        if not cls.is_mono:
            initial_padding = 2
        final_padding = max(char_info.right_padding for char_info in accepting_states)
        return cls(
            name,
            cls.get_space_width(image, is_bold, **kwargs),
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

    @classmethod
    @abstractmethod
    def get_input_columns(
        cls,
        image: SimpleImage,
        italic_offsets: set[int],
        is_bold: bool,
    ) -> Iterator[list[int]]:
        pass

    @classmethod
    @abstractmethod
    def get_space_width(cls, image: SimpleImage, is_bold: bool, **kwargs: Any) -> int:
        pass


class MonospaceFont(Font):
    @classmethod
    def get_input_columns(
        cls,
        image: SimpleImage,
        italic_offsets: set[int],
        is_bold: bool,
    ) -> Iterator[list[int]]:
        width = image.width // len(CHARS)
        height = image.height
        for i in itertools.count():
            columns = [
                get_column(width * i + j, 0, image, height, italic_offsets)
                for j in range(width)
            ]
            if is_bold:
                columns = [column1 | column2 for column1, column2 in zip([0] + columns, columns + [0])]
            yield columns

    @classmethod
    def get_space_width(cls, image: SimpleImage, is_bold: bool, **kwargs: Any) -> int:
        input_width = image.width // len(CHARS)
        return input_width + 1 if is_bold else input_width


@dataclass
class ProportionalFont(Font):
    is_mono: bool = False

    @classmethod
    def get_input_columns(
        cls,
        image: SimpleImage,
        italic_offsets: set[int],
        is_bold: bool,
    ) -> Iterator[list[int]]:
        height = image.height
        columns = []
        zero = False
        for x in range(image.width):
            column = get_column(x, 0, image, height, set())
            if column != 0:
                if zero:
                    columns.append(0)
                    zero = False
                columns.append(column)
            else:
                if zero:
                    yield columns
                    columns = []
                    zero = False
                if columns:
                    zero = True
        if columns:
            yield columns

    @classmethod
    def get_space_width(cls, image: SimpleImage, is_bold: bool, space_width: int = 0, **kwargs: Any) -> int:
        return space_width


def get_column(
    x0: int, y0: int, image: SimpleImage, height: int, italic_offsets: set[int], cut_bottom: int = 0, cut_top: int = 0
) -> int:
    bitmask = 0
    italic_offset = len(italic_offsets)
    for y in range(y0, y0 + height):
        if y - y0 in italic_offsets:
            italic_offset -= 1
        bitmask <<= 1
        if (x0 + italic_offset, y) in image.pixels:
            bitmask += 1
    return cut_column(bitmask, height, cut_bottom, cut_top)


def cut_column(column: int, height: int, cut_bottom: int = 0, cut_top: int = 0):
    bitmask = column
    if cut_bottom:
        bitmask = bitmask & -(1 << cut_bottom)
    if cut_top:
        bitmask = bitmask & ((1 << height - cut_top) - 1)
    return bitmask


def update_automaton(
    char: str,
    columns: list[int],
    automaton: FSA,
) -> CharInfo | None:
    x = 0
    while columns[x] == 0:
        x += 1
    left_padding = x
    x = len(columns) - 1
    while columns[x] == 0:
        x -= 1
    right_padding = len(columns) - 1 - x
    state = automaton
    for column in columns[left_padding:]:
        state = state.setdefault(column, {})
    # “ and ” look the same as " in some sizes,
    # but we prefer O to 0 and l to 1 when they look the same
    if ACCEPT not in state or char in ("O", "l"):
        state[ACCEPT] = CharInfo(char, left_padding, right_padding)
        return state[ACCEPT]


def get_pixels_from_columns(columns: list[int], height: int, x0: int, y0: int, italic_offsets: set[int]) -> set[Pixel]:
    pixels = set()
    for x, column in enumerate(columns, start=x0):
        italic_offset = 0
        for y in range(y0 + height - 1, y0 - 1, -1):
            if column == 0:
                break
            if column & 1 == 1:
                pixels.add(Pixel(x + italic_offset, y))
            if y - y0 in italic_offsets:
                italic_offset += 1
            column >>= 1
    return pixels


ALL_FONTS: list[Font] = [
    MonospaceFont.from_file(
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
    MonospaceFont.from_file(
        file_path_context_manager=as_file(files(parse_qwantz).joinpath(f'img/italic13.png')),
        name='Italic',
        italic_offsets={3, 5, 9, 11},
        is_bold=False,
        group='LC13',
        max_cut_bottom=0,
        max_cut_top=0,
    )
)

ALL_FONTS.append(
    ProportionalFont.from_file(
        file_path_context_manager=as_file(files(parse_qwantz).joinpath(f'img/serif15.png')),
        name='Serif',
        italic_offsets=set(),
        is_bold=False,
        group='TNR15',
        max_cut_bottom=0,
        max_cut_top=0,
        space_width=3,
    )
)
