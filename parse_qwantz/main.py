import hashlib
import logging
import sys
from dataclasses import dataclass
from logging import getLogger
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw

from parse_qwantz.box import Box, get_interval_distance
from parse_qwantz.color_logs import set_logging_formatter, ColorFormatter
from parse_qwantz.colors import Color
from parse_qwantz.lines import Line
from parse_qwantz.panel_overrides import get_panel_overrides
from parse_qwantz.text_blocks import get_text_blocks, TextBlock, sort_text_blocks
from parse_qwantz.elements import get_elements
from parse_qwantz.match_blocks import match_blocks
from parse_qwantz.match_lines import match_lines, Character, OFF_PANEL
from parse_qwantz.match_thought import match_thought
from parse_qwantz.pixels import Pixel, is_ask_professor_science
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
    [Character('T-Rex', (Box(Pixel(104, 90), Pixel(170, 238)),))],
    [
        Character('T-Rex', (
            Box(Pixel(30, 105), Pixel(75, 119)),
            Box(Pixel(4, 119), Pixel(105, 150)),
            Box(Pixel(4, 150), Pixel(60, 238)),
        )),
    ],
    [
        Character('T-Rex', (Box(Pixel(80, 55), Pixel(115, 213)), Box(Pixel(115, 75), Pixel(130, 90)))),
        Character('Dromiceiomimus', (Box(Pixel(325, 146), Pixel(357, 238)), Box(Pixel(250, 180), Pixel(325, 185)))),
    ],
    [
        Character('T-Rex', (Box(Pixel(0, 65), Pixel(30, 190)),)),
        Character('Utahraptor', (Box(Pixel(103, 81), Pixel(138, 165)), Box(Pixel(138, 140), Pixel(165, 180)))),
        Character('Girl', (Box(Pixel(0, 213), Pixel(8, 238)),)),
    ],
    [
        Character('T-Rex', (
            Box(Pixel(40, 70), Pixel(90, 103)),
            Box(Pixel(40, 104), Pixel(70, 140)),
            Box(Pixel(40, 141), Pixel(80, 180)),
        )),
        Character('T-Rex', (
            Box(Pixel(130, 155), Pixel(133, 210), inactive_sides=("left", "top", "bottom")),
            Box(Pixel(100, 197), Pixel(130, 213)),
        )),
        Character('Utahraptor', (
            Box(Pixel(198, 77), Pixel(233, 145)),
            Box(Pixel(225, 145), Pixel(250, 190)),
            Box(Pixel(185, 115), Pixel(198, 125)),
        )),
    ],
    [
        Character('T-Rex', (
            Box(Pixel(80, 64), Pixel(134, 84)),
            Box(Pixel(80, 84), Pixel(100, 169)),
            Box(Pixel(100, 84), Pixel(120, 120)),
            Box(Pixel(100, 110), Pixel(125, 120)),
        )),
    ],
]


@dataclass
class UnmatchedStuff:
    neighbors: list[tuple[TextLine, TextLine]]
    lines: list[Line]
    thoughts: list[Box]

    def __bool__(self):
        return bool(self.neighbors or self.lines or self.thoughts)


def parse_qwantz(image: Image, debug: bool, log_to_file: bool) -> Iterable[list[str]]:
    md5 = hashlib.md5(image.tobytes()).hexdigest()
    panel_overrides = get_panel_overrides().get(md5, {})
    masked, good_panels = prepare_image(image)
    for i, (panel, characters) in enumerate(zip(PANELS, CHARACTERS), start=1):
        if str(i) in panel_overrides:
            yield panel_overrides[str(i)]
            continue
        if i not in good_panels:
            logger.warning("Non-standard panel without an override")
            continue
        set_current_panel(i, log_to_file)
        (width, height), (x, y) = panel
        cropped = masked.crop((x, y, x + width, y + height))
        ask_professor_science = is_ask_professor_science(cropped)
        panel_image = SimpleImage.from_image(cropped, ask_professor_science)
        lines, thoughts, text_lines, extra_characters, unmatched_shapes = get_elements(panel_image)
        text_blocks, block_matches, thought_blocks, unmatched_stuff = match_stuff(
            characters + extra_characters, panel_image, lines, text_lines, thoughts
        )
        script_lines = get_script_lines(text_blocks, block_matches, thought_blocks, ask_professor_science)
        if debug and (unmatched_shapes or unmatched_stuff):
            handle_debug(cropped, text_blocks, unmatched_shapes, unmatched_stuff, characters + extra_characters)
        yield list(script_lines)


def get_unambiguous_words(image: Image) -> Iterable[str]:
    md5 = hashlib.md5(image.tobytes()).hexdigest()
    panel_overrides = get_panel_overrides().get(md5, {})
    masked, good_panels = prepare_image(image)
    for i, (panel, characters) in enumerate(zip(PANELS, CHARACTERS), start=1):
        if str(i) in panel_overrides:
            continue
        (width, height), (x, y) = panel
        cropped = masked.crop((x, y, x + width, y + height))
        panel_image = SimpleImage.from_image(cropped)
        lines, thoughts, text_lines, extra_characters, unmatched_shapes = get_elements(panel_image)
        text_blocks, block_matches, thought_blocks, unmatched_stuff = match_stuff(
            characters + extra_characters, panel_image, lines, text_lines, thoughts
        )
        for text_block in text_blocks:
            yield from text_block.unambiguous_words()


def match_stuff(
    characters: list[Character], image: SimpleImage, lines: list[Line], text_lines: list[TextLine], thoughts: list[Box]
) -> tuple[
    list[TextBlock],
    dict[TextBlock, list[Character]],
    list[TextBlock],
    UnmatchedStuff,
]:
    text_blocks = sort_text_blocks(get_text_blocks(text_lines))
    line_matches, unmatched_lines = match_lines(lines, text_blocks, characters, image)
    block_matches, text_blocks, unmatched_neighbors = match_blocks(line_matches, text_blocks)
    text_blocks = sort_text_blocks(text_blocks)
    unmatched_blocks = [block for block in text_blocks if block not in block_matches]
    thought_matches = list(match_thought(thoughts, unmatched_blocks))
    if thoughts and not thought_matches:
        logger.warning("Detected thought bubbles, but no thought text")
        unmatched_thoughts = thoughts
    else:
        unmatched_thoughts = []
    unmatched_blocks = [block for block in unmatched_blocks if block not in thought_matches]
    match_above_or_below(unmatched_blocks, block_matches)
    unmatched_stuff = UnmatchedStuff(unmatched_neighbors, unmatched_lines, unmatched_thoughts)
    return text_blocks, block_matches, thought_matches, unmatched_stuff


def get_script_lines(
    text_blocks: list[TextBlock],
    block_matches: dict[TextBlock, list[Character]],
    thought_blocks: list[TextBlock],
    ask_professor_science: bool,
) -> Iterable[str]:
    if ask_professor_science:
        yield "Sign: ASK PROFESSOR SCIENCE"
    for block in text_blocks:
        if god_or_devil := handle_god_and_devil(block, block_matches.get(block) == [OFF_PANEL]):
            block_matches[block] = [god_or_devil]
        if block in block_matches:
            characters = block_matches[block]
            if god_or_devil:
                content = block.content(mark_bold=False)
            elif characters[0].name == "Floating Batman head":
                content = block.content()
            else:
                content = block.content(include_font_name=True)
            yield f"{' and '.join(ch.name for ch in characters)}: {content}"
        elif block in thought_blocks:
            yield f"T-Rex: 〚thinks〛 {block.content()}"
        elif not block.font.is_mono:
            yield f"Text: {block.content()}"
        else:
            if not block.is_bold:
                logger.warning('Narrator not bold: %s', block.font.name)
            yield f"Narrator: {block.content(mark_bold=False)}"


def handle_debug(
    image: Image,
    text_blocks: list[TextBlock],
    unmatched_shapes: list[list[Pixel]],
    unmatched_stuff: UnmatchedStuff,
    characters: list[Character],
):
    draw = ImageDraw.Draw(image)
    for unmatched_shape in unmatched_shapes:
        box = get_box(unmatched_shape, padding=3)
        draw.rectangle(box, outline=(255, 0, 0))
        for pixel in unmatched_shape:
            draw.point(pixel, fill=(255, 0, 0))
    for thought_box in unmatched_stuff.thoughts:
        draw.rectangle(thought_box, outline=(255, 0, 255))
    for text_line1, text_line2 in unmatched_stuff.neighbors:
        box1 = text_line1.box()
        box2 = text_line2.box()
        draw.rectangle(box1, outline=(0, 0, 192))
        draw.rectangle(box2, outline=(0, 0, 192))
        draw.line([
            ((box1.left + box1.right) // 2, (box1.top + box1.bottom) // 2),
            ((box2.left + box2.right) // 2, (box2.top + box2.bottom) // 2),
        ], fill=(0, 0, 255))
    for line in unmatched_stuff.lines:
        draw.line(line, fill=(255, 0, 0))
        for block in text_blocks:
            for text_line in block.lines:
                box = text_line.box()
                draw.rectangle(box, outline=(0, 192, 0))
    if unmatched_stuff.neighbors or unmatched_stuff.lines:
        for character in characters:
            for box in character.boxes:
                draw.rectangle(box, outline=(0, 128, 0))
    image.show()


def match_above_or_below(unmatched_blocks: list[TextBlock], block_matches: dict[TextBlock, list[Character]]) -> None:
    for unmatched_block in unmatched_blocks:
        box = unmatched_block.box
        closest = None
        best_distance = None
        if not unmatched_block.is_bold:
            for block, characters in block_matches.items():
                if not characters:
                    continue
                if block.font.group != unmatched_block.font.group or block.color != unmatched_block.color:
                    continue
                other_box = block.box
                if get_interval_distance((box.left, box.right), (other_box.left, other_box.right)) == 0:
                    distance = max(other_box.top - box.bottom, box.top - other_box.bottom)
                    line_height = max(unmatched_block.font.height, block.font.height)
                    if distance < line_height * 2 and (best_distance is None or distance < best_distance):
                        closest = characters
                        best_distance = distance
        if closest:
            logger.warning("Matching disconnected blocks")
            block_matches[unmatched_block] = closest


def handle_god_and_devil(block: TextBlock, is_off_panel: bool) -> Character | None:
    if any(char.islower() for char in block.content()):
        return None
    if block.color == Color.RED and is_off_panel and block.is_bold:
        return Character.from_name('Devil')
    elif is_off_panel and block.is_bold:
        return Character.from_name('God')


def set_current_panel(panel: int | None = None, log_to_file: bool = False):
    panel_name = f" Panel {panel}:" if panel is not None else ""
    logger.handlers[0].setFormatter(ColorFormatter(defaults={"panel": panel_name}, colors=not log_to_file))


def main(
    input_file_path: Path,
    output_dir: Path | None = None,
    debug: bool = False,
    show_boxes: bool = False,
    unambiguous_words: bool = False,
):
    image = Image.open(input_file_path)
    if unambiguous_words:
        words = get_unambiguous_words(image)
        for word in words:
            print(word)
        return
    if output_dir:
        sys.stdout = (output_dir / (input_file_path.stem + '.txt')).open('w')
        logging.basicConfig(filename=output_dir / (input_file_path.stem + '.log'), filemode='w', force=True)
    for panel_no, panel in enumerate(parse_qwantz(image, debug=debug, log_to_file=bool(output_dir)), start=1):
        print(f'Panel {panel_no}:')
        for line in panel:
            print(line)
        if panel_no != 6:
            print()
    if show_boxes:
        draw = ImageDraw.Draw(image)
        for (panel, characters) in zip(PANELS, CHARACTERS):
            _, (x, y) = panel
            for character in characters:
                for box in character.boxes:
                    (x0, y0), (x1, y1), _ = box
                    draw.rectangle(((x0 + x, y0 + y), (x1 + x, y1 + y)), outline=(0, 128, 0))
        image.show()
