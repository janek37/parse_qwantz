from pathlib import Path

from PIL import Image

from character_shapes import REGULAR_FONT
from detect_text import get_text_blocks
from elements import get_elements
from match_lines import match_lines, Character
from pixels import SimpleImage


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


def parse_qwantz(directory: Path):
    for i in range(1, 7):
        filename = f"panel{i}.png"
        image = SimpleImage.from_image(Image.open(directory / filename))
        lines, text_lines = get_elements(image)
        text_blocks = sorted(get_text_blocks(text_lines, image), key=lambda b: (b.start[1], b.start[0]))
        print(filename)
        for block in text_blocks:
            if block.font != REGULAR_FONT:
                print(f"[{block.font}] {block.content}")
            else:
                print(block.content)
        for line, block1, block2 in match_lines(lines, text_blocks, CHARACTERS[i], image):
            print(line, str(block1), str(block2))


if __name__ == '__main__':
    import sys

    parse_qwantz(Path(sys.argv[1]))
