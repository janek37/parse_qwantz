from logging import getLogger
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw

from parse_qwantz.box import Box, get_interval_distance
from parse_qwantz.color_logs import set_logging_formatter
from parse_qwantz.colors import Color
from parse_qwantz.text_blocks import get_text_blocks, TextBlock
from parse_qwantz.elements import get_elements
from parse_qwantz.match_blocks import match_blocks, Character_s
from parse_qwantz.match_lines import match_lines, Character, OFF_PANEL, UnmatchedLine
from parse_qwantz.match_thought import match_thought
from parse_qwantz.pixels import Pixel
from parse_qwantz.shape import get_box
from parse_qwantz.simple_image import SimpleImage
from parse_qwantz.prepare_image import prepare_image
from parse_qwantz.text_lines import TextLine

set_logging_formatter()

logger = getLogger()

# size and offset
PANELS = [
    ((239, 239), (3, 2)),
    ((126, 239), (246, 2)),
    ((358, 239), (375, 2)),
    ((190, 239), (3, 244)),
    ((295, 239), (196, 244)),
    ((239, 239), (494, 244)),
]

CHARACTERS = [
    [Character('T-Rex', Box(Pixel(104, 90), Pixel(170, 238)))],
    [Character('T-Rex', Box(Pixel(4, 119), Pixel(105, 238)))],
    [
        Character('T-Rex', Box(Pixel(80, 55), Pixel(115, 213))),
        Character('Dromiceiomimus', Box(Pixel(325, 150), Pixel(357, 238))),
        Character('House', Box(Pixel(115, 210), Pixel(163, 238)), can_think=False),
    ],
    [
        Character('T-Rex', Box(Pixel(0, 65), Pixel(30, 190))),
        Character('Utahraptor', Box(Pixel(103, 81), Pixel(138, 165))),
        Character('Girl', Box(Pixel(0, 213), Pixel(8, 238)), can_think=False),
    ],
    [
        Character('T-Rex', Box(Pixel(40, 70), Pixel(96, 103))),
        Character('Utahraptor', Box(Pixel(200, 80), Pixel(233, 145))),
    ],
    [Character('T-Rex', Box(Pixel(74, 64), Pixel(120, 195)))],
]


def parse_qwantz(image: Image, debug: bool) -> Iterable[list[str]]:
    masked = prepare_image(image)
    for (panel, characters) in zip(PANELS, CHARACTERS):
        (width, height), (x, y) = panel
        cropped = masked.crop((x, y, x + width, y + height))
        panel_image = SimpleImage.from_image(cropped)
        try:
            script_lines, unmatched_shapes, unmatched_neighbors = parse_panel(panel_image, characters)
            if debug:
                draw = ImageDraw.Draw(cropped)
                for unmatched_shape in unmatched_shapes:
                    box = get_box(unmatched_shape, padding=3)
                    draw.rectangle(box, outline=(255, 0, 0))
                    for pixel in unmatched_shape:
                        draw.point(pixel, fill=(255, 0, 0))
                for text_line1, text_line2 in unmatched_neighbors:
                    box1 = text_line1.box()
                    box2 = text_line2.box()
                    draw.rectangle(box1, outline=(0, 0, 192))
                    draw.rectangle(box2, outline=(0, 0, 192))
                    draw.line([
                        ((box1.left + box1.right) // 2, (box1.top + box1.bottom) // 2),
                        ((box2.left + box2.right) // 2, (box2.top + box2.bottom) // 2),
                    ], fill=(0, 0, 255))
                if unmatched_shapes or unmatched_neighbors:
                    cropped.show()
            yield script_lines
        except UnmatchedLine as e:
            line, boxes, text_blocks = e.args
            if debug:
                draw = ImageDraw.Draw(cropped)
                for box, _character in boxes:
                    draw.rectangle(box, outline=(0, 192, 0))
                draw.line(line, fill=(255, 0, 0))
                cropped.show()
            yield ["Error"] + text_blocks


def parse_panel(
    image: Image, characters: list[Character]
) -> tuple[list[str], list[list[Pixel]], list[tuple[TextLine, TextLine]]]:
    lines, thoughts, text_lines, unmatched = get_elements(image)
    text_blocks = sorted(get_text_blocks(text_lines, image), key=lambda b: (b.end.y, b.end.x))
    line_matches = match_lines(lines, text_blocks, characters, image)
    block_matches, text_blocks, unmatched_neighbors = match_blocks(line_matches, text_blocks)
    text_blocks = sorted(text_blocks, key=lambda b: (b.end.y, b.end.x))
    unmatched_blocks = [block for block in text_blocks if block not in block_matches]
    thinking_characters = [character for character in characters if character.can_think]
    thought_matches = {
        block: character
        for block, character in match_thought(thoughts, unmatched_blocks, thinking_characters)
    }
    if thoughts and not thought_matches:
        logger.warning("Detected thought bubbles, but no thought text")
    unmatched_blocks = [block for block in unmatched_blocks if block not in thought_matches]
    match_above_or_below(unmatched_blocks, block_matches)
    script_lines = []
    for block in text_blocks:
        if god_or_devil := handle_god_and_devil(block, block_matches.get(block) == OFF_PANEL):
            block_matches[block] = god_or_devil
        if block in block_matches:
            character = block_matches[block]
            if isinstance(character, tuple):
                script_lines.append(f"{character[0]} and {character[1]}: {block.content(include_font_name=True)}")
            elif character.name in ('God', 'Devil'):
                script_lines.append(f"{character}: {block.content(mark_bold=False)}")
            else:
                script_lines.append(f"{character}: {block.content(include_font_name=True)}")
        elif block in thought_matches:
            character = thought_matches[block]
            script_lines.append(f"{character}: (thinks) {block.content()}")
        else:
            if not block.is_bold:
                logger.warning('Narrator not bold: %s', block.font.name)
            script_lines.append(f"Narrator: {block.content(mark_bold=False)}")
    return script_lines, unmatched, unmatched_neighbors


def match_above_or_below(unmatched_blocks: list[TextBlock], block_matches: dict[TextBlock, Character_s]) -> None:
    for unmatched_block in unmatched_blocks:
        box = unmatched_block.box
        closest = None
        best_distance = None
        if not unmatched_block.is_bold:
            for block, character in block_matches.items():
                other_box = block.box
                if get_interval_distance((box.left, box.right), (other_box.left, other_box.right)) == 0:
                    distance = max(other_box.top - box.bottom, box.top - other_box.bottom)
                    line_height = max(unmatched_block.font.height, block.font.height)
                    if distance < line_height * 2 and (best_distance is None or distance < best_distance):
                        closest = character
                        best_distance = distance
        if closest:
            block_matches[unmatched_block] = closest


def handle_god_and_devil(block: TextBlock, is_off_panel: bool):
    if block.color == Color.RED:
        if not is_off_panel:
            logger.warning('Red block not off-panel')
        if block.font.name != 'Bold':
            logger.warning('Red block not bold')
        return Character.from_name('Devil')
    elif is_off_panel and block.font.name == 'Bold':
        return Character.from_name('God')


def main(input_file_path: str | Path, debug: bool):
    for panel_no, panel in enumerate(parse_qwantz(Image.open(input_file_path), debug=debug), start=1):
        print(f'Panel {panel_no}:')
        for line in panel:
            print(line)
        if panel_no != 6:
            print()
