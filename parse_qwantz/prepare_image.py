from functools import cache
from importlib.resources import as_file
from pathlib import Path

from PIL import Image

DIM = (735, 500)

MASK_FILE_PATH = Path('parse_qwantz', 'img', 'mask.png')


@cache
def get_mask_image():
    with as_file(MASK_FILE_PATH) as image_path:
        return Image.open(image_path)


def apply_mask(image: Image):
    all_white = Image.new(mode='RGB', size=DIM, color=(255, 255, 255))
    return Image.composite(image, all_white, get_mask_image())
