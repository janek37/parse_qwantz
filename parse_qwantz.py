from typing import Iterable

from PIL import Image, ImageDraw

from box import Box
from colors import Color
from text_blocks import get_text_blocks, TextBlock
from elements import get_elements
from match_blocks import match_blocks
from match_lines import match_lines, Character, OFF_PANEL, UnmatchedLine
from match_thought import match_thought
from pixels import Pixel
from shape import get_box
from simple_image import SimpleImage
from prepare_image import apply_mask
from logger import get_logger

logger = get_logger()

# size and offset
PANELS = [
    ((239, 239), (3, 2)),
    ((126, 239), (246, 2)),
    ((358, 239), (375, 2)),
    ((190, 239), (3, 244)),
    ((295, 239), (196, 244)),
    ((239, 239), (494, 244)),
]

CHARACTERS = {
    1: [Character('T-Rex', Box(Pixel(104, 90), Pixel(170, 238)))],
    2: [Character('T-Rex', Box(Pixel(4, 119), Pixel(105, 238)))],
    3: [
        Character('T-Rex', Box(Pixel(80, 55), Pixel(115, 213))),
        Character('Dromiceiomimus', Box(Pixel(325, 150), Pixel(357, 238))),
        Character('House', Box(Pixel(115, 210), Pixel(163, 238)), can_think=False),
    ],
    4: [
        Character('T-Rex', Box(Pixel(0, 75), Pixel(50, 190))),
        Character('Utahraptor', Box(Pixel(103, 81), Pixel(138, 165))),
        Character('Girl', Box(Pixel(0, 213), Pixel(8, 238)), can_think=False),
    ],
    5: [
        Character('T-Rex', Box(Pixel(40, 70), Pixel(96, 103))),
        Character('Utahraptor', Box(Pixel(200, 80), Pixel(233, 145))),
    ],
    6: [Character('T-Rex', Box(Pixel(74, 64), Pixel(120, 195)))],
}


def parse_qwantz(image: Image) -> Iterable[list[str]]:
    masked = apply_mask(image)
    for i, (panel, characters) in enumerate(zip(PANELS, CHARACTERS), start=1):
        (width, height), (x, y) = panel
        cropped = masked.crop((x, y, x + width, y + height))
        panel_image = SimpleImage.from_image(cropped)
        try:
            script_lines, unmatched = parse_panel(panel_image, CHARACTERS[i])
            for unmatched_shape in unmatched:
                box = get_box(unmatched_shape, padding=3)
                draw = ImageDraw.Draw(cropped)
                draw.rectangle(box, outline=(255, 0, 0))
                for pixel in unmatched_shape:
                    draw.point(pixel, fill=(255, 0, 0))
                cropped.show()
            yield script_lines
        except UnmatchedLine as e:
            line, boxes, text_blocks = e.args
            draw = ImageDraw.Draw(cropped)
            for box, _character in boxes:
                draw.rectangle(box, outline=(0, 192, 0))
            draw.line(line, fill=(255, 0, 0))
            cropped.show()
            yield ["Error"] + text_blocks


def parse_panel(image: Image, characters: list[Character]) -> tuple[list[str], list[list[Pixel]]]:
    lines, thoughts, text_lines, unmatched = get_elements(image)
    text_blocks = sorted(get_text_blocks(text_lines, image), key=lambda b: (b.end.y, b.end.x))
    line_matches = match_lines(lines, text_blocks, characters, image)
    block_matches, text_blocks = match_blocks(line_matches, text_blocks)
    text_blocks = sorted(text_blocks, key=lambda b: (b.end.y, b.end.x))
    unmatched_blocks = [block for block in text_blocks if id(block) not in block_matches]
    thinking_characters = [character for character in characters if character.can_think]
    thought_matches = {
        id(block): character
        for block, character in match_thought(thoughts, unmatched_blocks, thinking_characters)
    }
    if thoughts and not thought_matches:
        logger.warning("Detected thought bubbles, but no thought text")
    script_lines = []
    for block in text_blocks:
        if god_or_devil := handle_god_and_devil(block, block_matches.get(id(block)) == OFF_PANEL):
            block_matches[id(block)] = god_or_devil
        if id(block) in block_matches:
            character = block_matches[id(block)]
            if isinstance(character, tuple):
                script_lines.append(f"{character[0]} and {character[1]}: {block}")
            elif character.name in ('God', 'Devil'):
                script_lines.append(f"{character}: {block.content(mark_bold=False)}")
            else:
                script_lines.append(f"{character}: {block}")
        elif id(block) in thought_matches:
            character = thought_matches[id(block)]
            script_lines.append(f"{character}: (thinks) {block.content()}")
        else:
            if not block.is_bold:
                logger.warning('Narrator not bold: %s', block.font.name)
            script_lines.append(f"Narrator: {block.content(mark_bold=False)}")
    return script_lines, unmatched


def handle_god_and_devil(block: TextBlock, is_off_panel: bool):
    if block.color == Color.RED:
        if not is_off_panel:
            logger.warning('Red block not off-panel')
        if block.font.name != 'Bold':
            logger.warning('Red block not bold')
        return Character.from_name('Devil')
    elif is_off_panel and block.font.name == 'Bold':
        return Character.from_name('God')


def main(input_file_path: str):
    for panel_no, panel in enumerate(parse_qwantz(Image.open(input_file_path)), start=1):
        print(f'Panel {panel_no}:')
        for line in panel:
            print(line)


if __name__ == '__main__':
    import sys
    main(sys.argv[1])
