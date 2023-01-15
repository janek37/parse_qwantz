import logging
from pathlib import Path
from typing import Iterable

from PIL import Image

from detect_text import get_text_blocks
from elements import get_elements
from match_blocks import match_blocks
from match_lines import match_lines, Character
from pixels import SimpleImage

logger = logging.getLogger()

CHARACTERS = {
    1: [Character('T-Rex', ((104, 99), (170, 238)))],
    2: [Character('T-Rex', ((4, 119), (105, 238)))],
    3: [
        Character('T-Rex', ((80, 55), (115, 213))),
        Character('Dromiceiomimus', ((325, 150), (357, 238))),
        Character('House', ((115, 210), (163, 238))),
    ],
    4: [
        Character('T-Rex', ((0, 77), (50, 190))),
        Character('Utahraptor', ((103, 81), (138, 190))),
        Character('Girl', ((0, 213), (8, 238))),
    ],
    5: [
        Character('T-Rex', ((40, 70), (70, 200))),
        Character('Utahraptor', ((200, 80), (233, 145))),
    ],
    6: [Character('T-Rex', ((74, 60), (107, 195)))],
}


def parse_qwantz(directory: Path) -> Iterable[Iterable[str]]:
    for i, characters in enumerate(CHARACTERS, start=1):
        image = SimpleImage.from_image(Image.open(directory / f"panel{i}.png"))
        yield parse_panel(image, CHARACTERS[i])


def parse_panel(image: Image, characters: list[Character]) -> Iterable[str]:
    lines, text_lines = get_elements(image)
    text_blocks = sorted(get_text_blocks(text_lines, image), key=lambda b: (b.start[1], b.start[0]))
    line_matches = match_lines(lines, text_blocks, characters, image)
    block_matches = match_blocks(line_matches)
    for block in text_blocks:
        if id(block) in block_matches:
            yield f"{block_matches[id(block)]}: {block}"
        else:
            if block.font.name != 'Bold':
                logger.warning('Narrator not bold')
            yield f"Narrator: {block.content}"


def main():
    import sys

    for panel_no, panel in enumerate(parse_qwantz(Path(sys.argv[1])), start=1):
        print(f'Panel {panel_no}:')
        for line in panel:
            print(line)


if __name__ == '__main__':
    main()
