import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib.resources import as_file, files
from itertools import islice, chain
from pathlib import Path
from typing import NamedTuple, ContextManager, Iterator, ForwardRef, Union, Any, Sequence

from PIL import Image

import parse_qwantz
from parse_qwantz.box import Box
from parse_qwantz.char_variants import VARIANTS
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage

CHARS = (
    "0123456789"
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    """!"#$%&'()*+,-./:;<=>?@[]^{|}‘’“”·•™"""
    "éÉïçêáÁèÈàßûñùÜóÆÖИÇâæÊöü"
    "°®♪♫±_~¡²«»∩×"
    "αάβγδεέζηήθιίκλμνξοόπρσςτυύφχψωώˣ"
)
FORBIDDEN_FIRST_CHARS = "%)=^|}”·™_"

ACCEPT = -1

FONT_SIZES = [
    (13, 'Regular', 8, 2, 1, None),
    (12, 'Condensed', 7, 0, 0, None),
    (11, 'Small', 7, 0, 0, "small"),
    (10, 'Petite', 6, 0, 0, "small"),
    (9, 'Mini', 5, 0, 0, "tiny"),
    (8, 'Tiny', 5, 0, 0, "tiny"),
]


@dataclass
class CharInfo:
    char: str
    left_padding: int
    right_padding: int
    extra_info: str | None = None


class CharBox(NamedTuple):
    char: str
    box: Box
    is_bold: bool
    is_italic: bool
    pixels: set[Pixel]
    extra_info: str | None = None

    def with_box(self, box: Box):
        return CharBox(self.char, box, self.is_bold, self.is_italic, self.pixels)

    def with_char(self, char: str):
        return CharBox(char, self.box, self.is_bold, self.is_italic, self.pixels)

    @classmethod
    def space(cls, is_bold: bool, is_italic: bool, box: Box | None = None) -> "CharBox":
        return cls(
            char=' ',
            box=box or Box.dummy(),
            is_bold=is_bold,
            is_italic=is_italic,
            pixels=set(),
        )


FSA_BACKREF = ForwardRef("FSA")

FSA = dict[int, Union[FSA_BACKREF, CharInfo]]


@dataclass
class Font(ABC):
    name: str
    space_width: int
    height: int
    base: int
    automaton: FSA
    initial_padding: int
    final_padding: int
    is_bold: bool
    italic_offsets: set[int]
    group: str
    max_cut_bottom: int
    max_cut_top: int
    display_name: str | None = None
    is_mono: bool = True

    base_left_padding: int = 0
    base_right_padding: int = 0
    skip_chars: Sequence[str] = ()

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
        if first_column is not None:
            pixel = Pixel(pixel.x - 1, pixel.y)
            columns = chain([(pixel.x, first_column)], columns)
        x = column = 0  # to satisfy linters; columns are never empty
        for x, column in islice(columns, self.initial_padding + 1):
            if column != 0:
                break
        else:
            for x, column in columns:
                if column != 0:
                    char_box = CharBox.space(
                        self.is_bold,
                        is_italic,
                        Box(pixel, Pixel(x, pixel.y + self.height)),
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
                    if actual_column != ACCEPT and ACCEPT in next_state and column | actual_column == column:
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
            if not accepted:
                return None, None
        x, char_info, complement, char_columns = accepted
        if is_first and char_info.char in FORBIDDEN_FIRST_CHARS:
            return None, None
        if char_info.left_padding < 0 and x0 - char_info.left_padding - pixel.x >= self.initial_padding:
            return CharBox.space(
                self.is_bold,
                is_italic,
                Box(pixel, Pixel(x0 - char_info.left_padding, pixel.y + self.height)),
            ), char_columns[0]
        pixels = get_pixels_from_columns(char_columns, self.height, x0, pixel.y, self.italic_offsets)
        if char_info.right_padding < 0 and complement is None:
            complement = 0
        return CharBox(
            char_info.char,
            Box(
                Pixel(x0 - char_info.left_padding, pixel.y),
                Pixel(x + 1, pixel.y + self.height),
            ),
            self.is_bold,
            is_italic,
            pixels,
            char_info.extra_info,
        ), complement

    def _get_columns(
        self, pixel: Pixel,
        image: SimpleImage,
        cut_bottom: int = 0,
        cut_top: int = 0,
    ) -> Iterator[tuple[int, int]]:
        max_x = image.width + self.final_padding
        if self.is_mono:
            max_x = min(max_x, pixel.x + self.space_width * 2 + 1)
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
        width: int,
        italic_offsets: set[int],
        is_bold: bool,
        group: str,
        max_cut_bottom: int,
        max_cut_top: int,
        display_name: str | None = None,
        **kwargs: Any,
    ) -> "Font":
        with file_path_context_manager as file_path:
            image = SimpleImage.from_image(Image.open(file_path))
        height = image.height
        automaton: FSA = {}
        accepting_states: list[CharInfo] = []
        base = 0  # unused value
        for i, (char, columns) in enumerate(zip(CHARS, cls.get_input_columns(image, width, italic_offsets, is_bold))):
            if char in cls.skip_chars:
                continue
            if char == '0':
                for y in range(height - 1, 0, -1):
                    if any((1 << (height - 1 - y)) & column for column in columns):
                        base = y
                        break
            if maybe_char_info := cls.update_automaton(char, columns, automaton):
                accepting_states.append(maybe_char_info)
        for char, columns in VARIANTS.get((name, is_bold), []):
            variant_hash = hash(tuple(columns)) & ((2 << 32) - 1)
            maybe_char_info = cls.update_automaton(
                char, columns, automaton, extra_info=f"{name}-{'bold' if is_bold else 'normal'}-{char}-{variant_hash:x}"
            )
            if maybe_char_info:
                accepting_states.append(maybe_char_info)
        initial_padding = max(char_info.left_padding for char_info in accepting_states)
        if not cls.is_mono:
            initial_padding = 2
        final_padding = max(char_info.right_padding for char_info in accepting_states)
        return cls(
            name,
            cls.get_space_width(image, width, is_bold, **kwargs),
            height,
            base,
            automaton,
            initial_padding,
            final_padding,
            is_bold,
            italic_offsets,
            group,
            max_cut_bottom,
            max_cut_top,
            display_name,
        )

    @classmethod
    @abstractmethod
    def get_input_columns(
        cls,
        image: SimpleImage,
        width: int,
        italic_offsets: set[int],
        is_bold: bool,
    ) -> Iterator[list[int]]:
        pass

    @classmethod
    @abstractmethod
    def get_space_width(cls, image: SimpleImage, width: int, is_bold: bool, **kwargs: Any) -> int:
        pass

    @classmethod
    def update_automaton(
        cls,
        char: str,
        columns: list[int],
        automaton: FSA,
        extra_info: str | None = None,
    ) -> CharInfo | None:
        x = 0
        while columns[x] == 0:
            x += 1
        left_padding = cls.base_left_padding + x
        x = len(columns) - 1
        while columns[x] == 0:
            x -= 1
        right_padding = cls.base_right_padding + len(columns) - 1 - x
        state = automaton
        from_column = left_padding - cls.base_left_padding
        if cls.is_mono:
            to_column = len(columns)
        else:
            to_column = len(columns) + (cls.base_right_padding if right_padding >= 0 else 0)
        for i, column in enumerate(columns[from_column:to_column]):
            state = state.setdefault(column, {})
            if right_padding > 1 and i >= len(columns) - right_padding - 1:
                if ACCEPT not in state or char in ("O", "l"):
                    state[ACCEPT] = CharInfo(char, left_padding, len(columns) - i, extra_info)
        # “ and ” look the same as " in some sizes,
        # but we prefer O to 0 and l to 1 when they look the same
        if ACCEPT not in state or char in ("O", "l"):
            state[ACCEPT] = CharInfo(char, left_padding, right_padding, extra_info)
            return state[ACCEPT]


class MonospaceFont(Font):
    @classmethod
    def get_input_columns(
        cls,
        image: SimpleImage,
        width: int,
        italic_offsets: set[int],
        is_bold: bool,
    ) -> Iterator[list[int]]:
        height = image.height
        for i in itertools.count():
            if width * (i+1) > image.width:
                return
            columns = [
                get_column(width * i + j, 0, image, height, italic_offsets)
                for j in range(width)
            ]
            if is_bold:
                columns = [column1 | column2 for column1, column2 in zip([0] + columns, columns + [0])]
            yield columns

    @classmethod
    def get_space_width(cls, image: SimpleImage, width: int, is_bold: bool, **kwargs: Any) -> int:
        return width + 1 if is_bold else width


@dataclass
class ProportionalFont(Font):
    is_mono: bool = False
    separator: int = 8
    prev_column_mask: int = 28
    base_left_padding: int = -1
    base_right_padding: int = -1
    skip_chars = ["1"]  # hard to distinguish from "l"

    @classmethod
    def get_input_columns(
        cls,
        image: SimpleImage,
        width: int,
        italic_offsets: set[int],
        is_bold: bool,
    ) -> Iterator[list[int]]:
        height = image.height
        columns = []
        first_column = True
        previous_column = 0
        for x in range(image.width):
            column = get_column(x, 0, image, height, set())
            if not first_column and column == cls.separator and previous_column & cls.prev_column_mask == 0:
                yield columns
                columns = []
                first_column = True
            else:
                columns.append(column)
                if column != 0:
                    first_column = False
            previous_column = column
        if columns:
            yield columns

    @classmethod
    def get_space_width(cls, image: SimpleImage, width: int, is_bold: bool, space_width: int = 0, **kwargs: Any) -> int:
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
        width=width,
        italic_offsets=set(),
        is_bold=is_bold,
        group=f'LC{size}',
        max_cut_bottom=max_cut_bottom,
        max_cut_top=max_cut_top,
        display_name=display_name,
    )
    for size, name, width, max_cut_bottom, max_cut_top, display_name in FONT_SIZES
    for is_bold in (False, True)
]

ALL_FONTS.append(
    MonospaceFont.from_file(
        file_path_context_manager=as_file(files(parse_qwantz).joinpath(f'img/italic13.png')),
        name='Italic',
        width=8,
        italic_offsets={3, 5, 9, 11},
        is_bold=False,
        group='LC13',
        max_cut_bottom=0,
        max_cut_top=0,
    )
)

ALL_FONTS.append(
    ProportionalFont.from_file(
        file_path_context_manager=as_file(files(parse_qwantz).joinpath(f'img/serif13.png')),
        name='Serif',
        width=0,
        italic_offsets=set(),
        is_bold=False,
        group='TNR13',
        max_cut_bottom=0,
        max_cut_top=0,
        space_width=3,
        display_name='serif'
    )
)
