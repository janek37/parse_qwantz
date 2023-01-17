from typing import Iterable

from PIL import Image, ImageDraw

from colors import Color
from detect_blocks import get_text_blocks
from elements import get_elements, NoMatchFound
from match_blocks import match_blocks
from match_lines import match_lines, Character, OFF_PANEL
from pixels import SimpleImage
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
    1: [Character('T-Rex', ((104, 90), (170, 238)))],
    2: [Character('T-Rex', ((4, 119), (105, 238)))],
    3: [
        Character('T-Rex', ((80, 55), (115, 213))),
        Character('Dromiceiomimus', ((325, 150), (357, 238))),
        Character('House', ((115, 210), (163, 238))),
    ],
    4: [
        Character('T-Rex', ((0, 77), (50, 190))),
        Character('Utahraptor', ((103, 81), (138, 165))),
        Character('Girl', ((0, 213), (8, 238))),
    ],
    5: [
        Character('T-Rex', ((40, 70), (70, 200))),
        Character('Utahraptor', ((200, 80), (233, 145))),
    ],
    6: [Character('T-Rex', ((74, 60), (107, 195)))],
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


def parse_panel(image: Image, characters: list[Character]) -> Iterable[str]:
    lines, text_lines = get_elements(image)
    text_blocks = sorted(get_text_blocks(text_lines, image), key=lambda b: (b.start[1], b.start[0]))
    line_matches = match_lines(lines, text_blocks, characters, image)
    block_matches = match_blocks(line_matches)
    for block in text_blocks:
        if block.color == Color.RED:
            if block_matches.get(id(block)) != OFF_PANEL:
                logger.warning('Red block not off-panel')
            if block.font.name != 'Bold':
                logger.warning('Red block not bold')
            block_matches[id(block)] = Character('Devil', ((0, 0), (0, 0)))
        elif block_matches.get(id(block)) == OFF_PANEL and block.font.name == 'Bold':
            block_matches[id(block)] = Character('God', ((0, 0), (0, 0)))
        if id(block) in block_matches:
            character = block_matches[id(block)]
            if character.name in ('God', 'Devil'):
                yield f"{character}: {block.content}"
            else:
                yield f"{character}: {block}"
        else:
            if block.font.name != 'Bold':
                logger.warning('Narrator not bold')
            yield f"Narrator: {block.content}"


def main():
    import sys

    for panel_no, panel in enumerate(parse_qwantz(Image.open(sys.argv[1])), start=1):
        print(f'Panel {panel_no}:')
        for line in panel:
            print(line)


if __name__ == '__main__':
    main()
