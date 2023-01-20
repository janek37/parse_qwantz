from typing import Iterable

from PIL import Image, ImageDraw

from colors import Color
from detect_blocks import get_text_blocks, TextBlock
from elements import get_elements, NoMatchFound
from match_blocks import match_blocks
from match_lines import match_lines, Character, OFF_PANEL, UnmatchedLine
from pixels import SimpleImage, Pixel
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
    1: [Character('T-Rex', (Pixel(104, 90), Pixel(170, 238)))],
    2: [Character('T-Rex', (Pixel(4, 119), Pixel(105, 238)))],
    3: [
        Character('T-Rex', (Pixel(80, 55), Pixel(115, 213))),
        Character('Dromiceiomimus', (Pixel(325, 150), Pixel(357, 238))),
        Character('House', (Pixel(115, 210), Pixel(163, 238))),
    ],
    4: [
        Character('T-Rex', (Pixel(0, 77), Pixel(50, 190))),
        Character('Utahraptor', (Pixel(103, 81), Pixel(138, 165))),
        Character('Girl', (Pixel(0, 213), Pixel(8, 238))),
    ],
    5: [
        Character('T-Rex', (Pixel(40, 70), Pixel(70, 200))),
        Character('T-Rex', (Pixel(66, 70), Pixel(96, 103))),
        Character('Utahraptor', (Pixel(200, 80), Pixel(233, 145))),
    ],
    6: [Character('T-Rex', (Pixel(74, 64), Pixel(120, 195)))],
}


def parse_qwantz(image: Image) -> Iterable[list[str]]:
    masked = apply_mask(image)
    for i, (panel, characters) in enumerate(zip(PANELS, CHARACTERS), start=1):
        (width, height), (x, y) = panel
        cropped = masked.crop((x, y, x + width, y + height))
        panel_image = SimpleImage.from_image(cropped)
        try:
            yield list(parse_panel(panel_image, CHARACTERS[i]))
        except NoMatchFound as e:
            (x0, y0), text_lines = e.args
            draw = ImageDraw.Draw(cropped)
            draw.rectangle(((x0 - 13, y0 - 13), (x0 + 13), (y0 + 13)), outline=(255, 0, 0))
            cropped.show()
            yield ["Error"] + text_lines
        except UnmatchedLine as e:
            line, boxes, text_blocks = e.args
            draw = ImageDraw.Draw(cropped)
            for box, _character in boxes:
                draw.rectangle(box, outline=(0, 192, 0))
            draw.line(line, fill=(255, 0, 0))
            cropped.show()
            yield ["Error"] + text_blocks


def parse_panel(image: Image, characters: list[Character]) -> Iterable[str]:
    lines, text_lines = get_elements(image)
    text_blocks = sorted(get_text_blocks(text_lines, image), key=lambda b: (b.end[1], b.end[0]))
    line_matches = match_lines(lines, text_blocks, characters, image)
    block_matches = match_blocks(line_matches)
    for block in text_blocks:
        if god_or_devil := handle_god_and_devil(block, block_matches.get(id(block)) == OFF_PANEL):
            block_matches[id(block)] = god_or_devil
        if id(block) in block_matches:
            character = block_matches[id(block)]
            if isinstance(character, tuple):
                yield f"{character[0]} and {character[1]}: {block}"
            elif character.name in ('God', 'Devil'):
                yield f"{character}: {block.content}"
            else:
                yield f"{character}: {block}"
        else:
            if block.font.name != 'Bold':
                logger.warning('Narrator not bold: %s', block.font.name)
            yield f"Narrator: {block.content}"


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
