import logging
import math
from importlib.resources import files
from itertools import chain
from typing import Iterator
from xml.etree import ElementTree

from PIL import Image

import parse_qwantz
from parse_qwantz.colors import Color
from parse_qwantz.elements import get_elements, Direction
from parse_qwantz.fonts import CharBox, Font
from parse_qwantz.lines import Line
from parse_qwantz.match_lines import Character
from parse_qwantz.panels import PANELS
from parse_qwantz.pixels import is_ask_professor_science, Pixel
from parse_qwantz.prepare_image import prepare_image
from parse_qwantz.simple_image import SimpleImage

logger = logging.getLogger()

BLANK_FILE_PATH = files(parse_qwantz).joinpath('img/blank.svg')
ASK_PROFESSOR_SCIENCE_PATH = files(parse_qwantz).joinpath('img/ask-professor-science.svg')
BATMAN_LEFT_PATH = files(parse_qwantz).joinpath('img/batman-left.svg')
BATMAN_RIGHT_PATH = files(parse_qwantz).joinpath('img/batman-right.svg')


def generate_svg(image: Image):
    masked, good_panels = prepare_image(image)
    ask_professor_science = _is_ask_professor_science(masked)
    simple_image = SimpleImage.from_image(masked, ask_professor_science)
    lines, char_boxes, characters = get_elements_for_svg(simple_image)
    svg_elements = [make_line_element(line, width, i) for i, (line, width) in enumerate(lines)]
    svg_elements.extend(
        chain(*(make_text_element(char_box, font, color, i) for i, (char_box, font, color) in enumerate(char_boxes)))
    )
    svg_elements.extend((make_character(character) for character in characters))
    if ask_professor_science:
        svg_elements.append(get_professor_science_sign())
    return render_svg(svg_elements)


def _is_ask_professor_science(image: Image) -> bool:
    panel = PANELS[0]
    (width, height), (x, y) = panel
    cropped = image.crop((x, y, x + width, y + height))
    return is_ask_professor_science(cropped)


def get_professor_science_sign() -> ElementTree.Element:
    doc = ElementTree.parse(ASK_PROFESSOR_SCIENCE_PATH)
    root = doc.getroot()
    return root[0]


def get_batman(direction: Direction) -> ElementTree.Element:
    batman_path = BATMAN_LEFT_PATH if direction == Direction.LEFT else BATMAN_RIGHT_PATH
    doc = ElementTree.parse(batman_path)
    root = doc.getroot()
    return root[0]


def render_svg(svg_elements: list[ElementTree.Element]) -> str:
    ElementTree.register_namespace('', "http://www.w3.org/2000/svg")
    ElementTree.register_namespace('rdf', "http://www.w3.org/1999/02/22-rdf-syntax-ns#")
    ElementTree.register_namespace('cc', "http://creativecommons.org/ns#")
    doc = ElementTree.parse(BLANK_FILE_PATH)
    root = doc.getroot()
    root.extend(svg_elements)
    return ElementTree.tostring(root).decode()


def make_line_element(line: Line, width: int, no: int) -> ElementTree.Element:
    line_element = ElementTree.Element(
        "line",
        {
            "id": f"line{no}",
            "x1": str(line[0].x + 0.5),
            "y1": str(line[0].y + 0.5),
            "x2": str(line[1].x + 0.5),
            "y2": str(line[1].y + 0.5),
            "stroke": "black",
            "stroke-width": str(width),
        }
    )
    line_element.tail = "\n"
    return line_element


def make_text_element(char_box: CharBox, font: Font, color: Color, no: int) -> Iterator[ElementTree.Element]:
    font_family = "Times New Roman" if font.group == "TNR13" else "Lucida Console"
    x = char_box.box.left
    if char_box.is_italic:
        x += len(font.italic_offsets) / 2
    if char_box.is_bold:
        xs = [x, x + 0.25, x + 0.5, x + 0.75]
    else:
        xs = [x]
    for x in xs:
        attrib = {
            "id": f"text{no}",
            "x": str(x),
            "y": str(char_box.box.bottom - (font.height - font.base - 1)),
            "fill": f"#{color.red:02X}{color.green:02X}{color.blue:02X}"
        }
        styling = [
            f"font-family: {font_family};",
            f"font-size: {font.height}px;",
        ]
        if char_box.is_italic:
            styling.append("font-style: italic;")
        if styling:
            attrib["style"] = " ".join(styling)
        text_element = ElementTree.Element("text", attrib)
        text_element.text = char_box.char
        text_element.tail = "\n"
        yield text_element


def make_character(character: Character) -> ElementTree.Element:
    assert character.name == "Floating Batman head", character.name
    batman = get_batman(character.direction)
    box = character.boxes[0]
    attrib = {
        "id": "batman",
        "transform": f"translate({box.left},{box.top})"
    }
    group_element = ElementTree.Element("g", attrib)
    group_element.append(batman)
    return group_element


def get_elements_for_svg(
    image: SimpleImage
) -> tuple[list[tuple[Line, int]], list[tuple[CharBox, Font, Color]], list[Character]]:
    lines, line_widths, thoughts, text_lines, extra_characters, unmatched = get_elements(image)
    if thoughts or unmatched:
        logger.warning(f"Foreign elements in the image")
    char_boxes = [
        (char_box, text_line.font, text_line.color)
        for text_line in text_lines
        for char_box in text_line.char_boxes
        if char_box.pixels
    ]
    lines = (fix_for_panel_edges(line) for line in lines)
    return list(zip(lines, line_widths)), char_boxes, extra_characters


def fix_for_panel_edges(line: Line) -> Line:
    start, end = line
    length = math.sqrt((start.x - end.x)**2 + (start.y - end.y)**2)
    return _get_new_end(start, end, length), _get_new_end(end, start, length)


def _get_new_end(end: Pixel, other_end: Pixel, length: float) -> Pixel:
    if any(is_on_edge(end, panel) for panel in PANELS):
        return Pixel(
            x=int(end.x + 2 * (end.x - other_end.x) / length),
            y=int(end.y + 2 * (end.y - other_end.y) / length)
        )
    else:
        return end


def is_on_edge(pixel: Pixel, panel: tuple[tuple[int, int], tuple[int, int]]) -> bool:
    (width, height), (x, y) = panel
    return (
        (x <= pixel.x < x + width and pixel.y in (y, y + height - 1))
        or (y <= pixel.y < y + height and pixel.x in (x, x + width - 1))
    )
