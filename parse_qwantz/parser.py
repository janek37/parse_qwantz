import hashlib
import logging
from dataclasses import dataclass
from typing import Iterable

from PIL import Image, ImageDraw

from parse_qwantz import colors
from parse_qwantz.box import Box, get_interval_distance
from parse_qwantz.color_logs import ColorFormatter
from parse_qwantz.elements import get_elements
from parse_qwantz.lines import Line
from parse_qwantz.match_blocks import match_blocks
from parse_qwantz.match_lines import Character, match_lines, OFF_PANEL
from parse_qwantz.match_thought import match_thought
from parse_qwantz.panels import PANELS, CHARACTERS, FOOTER
from parse_qwantz.panel_overrides import get_panel_overrides
from parse_qwantz.pixels import is_ask_professor_science, Pixel
from parse_qwantz.prepare_image import prepare_image
from parse_qwantz.shape import get_box
from parse_qwantz.simple_image import SimpleImage
from parse_qwantz.text_blocks import TextBlock, sort_text_blocks, get_text_blocks
from parse_qwantz.text_lines import TextLine

logger = logging.getLogger()


def parse_qwantz(
    image: Image, debug: bool = False, log_colors: bool = False, ignore_overrides: bool = False
) -> Iterable[list[str]]:
    md5 = hashlib.md5(image.tobytes()).hexdigest()
    panel_overrides = get_panel_overrides().get(md5, {}) if not ignore_overrides else {}
    masked, good_panels = prepare_image(image)
    for i, (panel, characters) in enumerate(zip(PANELS, CHARACTERS), start=1):
        if str(i) in panel_overrides:
            yield panel_overrides[str(i)]
            continue
        if i not in good_panels:
            logger.warning("Non-standard panel without an override")
            continue
        set_current_panel(i, log_colors)
        (width, height), (x, y) = panel
        cropped = masked.crop((x, y, x + width, y + height))
        ask_professor_science = is_ask_professor_science(cropped)
        panel_image = SimpleImage.from_image(cropped, ask_professor_science)
        lines, _widths, thoughts, text_lines, extra_characters, unmatched_shapes = get_elements(panel_image)
        text_blocks, block_matches, thought_blocks, unmatched_stuff = match_stuff(
            characters + extra_characters, panel_image, lines, text_lines, thoughts
        )
        for text_block in text_blocks:
            for extra_info in text_block.extra_info():
                logger.warning(f"Variant used: {extra_info}")
        script_lines = list(get_script_lines(text_blocks, block_matches, thought_blocks, ask_professor_science))
        if debug and (unmatched_shapes or unmatched_stuff):
            handle_debug(cropped, text_blocks, unmatched_shapes, unmatched_stuff, characters + extra_characters)
        if script_lines:
            yield list(script_lines)
        else:
            yield ["〚no text〛"]


def parse_footer(image: Image) -> list[str]:
    md5 = hashlib.md5(image.tobytes()).hexdigest()
    panel_overrides = get_panel_overrides().get(md5, {})
    if "footer" in panel_overrides:
        return panel_overrides["footer"]
    masked, _ = prepare_image(image)
    (width, height), (x, y) = FOOTER
    cropped = masked.crop((x, y, x + width, y + height))
    footer_image = SimpleImage.from_image(cropped)
    lines, _widths, thoughts, text_lines, extra_characters, unmatched_shapes = get_elements(footer_image)
    if lines or thoughts or extra_characters or unmatched_shapes:
        logger.warning("Unexpected elements in footer")
    for text_line in text_lines:
        for char_box in text_line.char_boxes:
            if char_box.extra_info:
                logger.warning(f"Variant used: {char_box.extra_info}")
    return [text_line.content for text_line in text_lines]


def set_current_panel(panel: int, use_colors: bool = True):
    panel_name = f" Panel {panel}:"
    if not logger.handlers:
        logging.basicConfig()
    logger.handlers[0].setFormatter(ColorFormatter(defaults={"panel": panel_name}, colors=use_colors))


@dataclass
class UnmatchedStuff:
    neighbors: list[tuple[TextLine, TextLine]]
    lines: list[Line]
    thoughts: list[Box]

    def __bool__(self):
        return bool(self.neighbors or self.lines or self.thoughts)


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
                if god_or_devil.name in ("God", "Devil"):
                    content = block.content(mark_bold=False)
                else:
                    content = block.content(mark_italic=False)
            elif characters[0].name == "Floating Batman head":
                content = block.content()
            else:
                content = block.content(include_font_name=True)
            line = f"{' and '.join(ch.name for ch in characters)}: {content}"
            if not line[0].isupper():
                line = line[0].upper() + line[1:]
            yield line
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
        draw.rectangle(box[:2], outline=(255, 0, 0))
        for pixel in unmatched_shape:
            draw.point(pixel, fill=(255, 0, 0))
    for thought_box in unmatched_stuff.thoughts:
        draw.rectangle(thought_box[:2], outline=(255, 0, 255))
    for text_line1, text_line2 in unmatched_stuff.neighbors:
        box1 = text_line1.box()
        box2 = text_line2.box()
        draw.rectangle(box1[:2], outline=(0, 0, 192))
        draw.rectangle(box2[:2], outline=(0, 0, 192))
        draw.line([
            ((box1.left + box1.right) // 2, (box1.top + box1.bottom) // 2),
            ((box2.left + box2.right) // 2, (box2.top + box2.bottom) // 2),
        ], fill=(0, 0, 255))
    for line in unmatched_stuff.lines:
        draw.line(line, fill=(255, 0, 0))
        for block in text_blocks:
            for text_line in block.lines:
                box = text_line.box()
                draw.rectangle(box[:2], outline=(0, 192, 0))
    if unmatched_stuff.neighbors or unmatched_stuff.lines:
        for character in characters:
            for box in character.boxes:
                draw.rectangle(box[:2], outline=(0, 128, 0))
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
    if block.color == colors.RED and is_off_panel and block.is_bold:
        return Character.from_name('Devil')
    elif is_off_panel and block.is_bold:
        return Character.from_name('God')
    elif is_off_panel and block.is_italic:
        return Character.from_name('Creepy voice(s)')
