import hashlib
import logging
import sys
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw

from parse_qwantz.panel_overrides import get_panel_overrides
from parse_qwantz.panels import PANELS, CHARACTERS
from parse_qwantz.parser import parse_qwantz, match_stuff, parse_footer
from parse_qwantz.elements import get_elements
from parse_qwantz.simple_image import SimpleImage
from parse_qwantz.prepare_image import prepare_image
from parse_qwantz.svg_gen import generate_svg


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
        lines, _widths, thoughts, text_lines, extra_characters, unmatched_shapes = get_elements(panel_image)
        text_blocks, block_matches, thought_blocks, unmatched_stuff = match_stuff(
            characters + extra_characters, panel_image, lines, text_lines, thoughts
        )
        for text_block in text_blocks:
            yield from text_block.unambiguous_words()


def main(
    input_file_path: Path,
    output_dir: Path | None = None,
    debug: bool = False,
    show_boxes: bool = False,
    unambiguous_words: bool = False,
    svg: bool = False,
    footer: bool = False,
):
    image = Image.open(input_file_path)
    if unambiguous_words:
        words = get_unambiguous_words(image)
        for word in words:
            print(word)
        return
    if svg:
        print(generate_svg(image))
        return
    if output_dir:
        sys.stdout = (output_dir / (input_file_path.name + '.txt')).open('w')
        logging.basicConfig(filename=output_dir / (input_file_path.stem + '.log'), filemode='w', force=True)
    if footer:
        for line in parse_footer(image):
            print(line)
        return
    for panel_no, lines in enumerate(parse_qwantz(image, debug=debug, log_colors=not output_dir), start=1):
        for line in lines:
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
    sys.stdout.flush()
