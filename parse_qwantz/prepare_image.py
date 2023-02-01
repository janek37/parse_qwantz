import logging
import sys
from functools import cache
from importlib.resources import as_file
from pathlib import Path

from PIL import Image

logger = logging.getLogger()

DIM = (735, 500)

MASK_FILE_PATH = Path('parse_qwantz', 'img', 'mask.png')

SAMPLE = [
    ((113, 183), (128, 255, 64)),
    ((704, 183), (255, 242, 179)),
    ((452, 405), (255, 191, 82)),
    ((290, 160), (255, 128, 161)),
    ((372, 484), (0, 0, 0)),
]


@cache
def get_mask_image():
    with as_file(MASK_FILE_PATH) as image_path:
        return Image.open(image_path)


def prepare_image(image: Image):
    if image.size != DIM:
        logger.error(f"Wrong image dimensions: {image.size}, only {DIM} is valid")
        sys.exit(1)
    for pixel, color in SAMPLE:
        if image.getpixel(pixel) != color:
            logger.error("Invalid template")
            sys.exit(1)
    all_white = Image.new(mode='RGB', size=DIM, color=(255, 255, 255))
    return Image.composite(image, all_white, get_mask_image())
