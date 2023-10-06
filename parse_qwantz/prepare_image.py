import logging
from functools import cache
from importlib.resources import as_file, files

from PIL import Image

import parse_qwantz
from parse_qwantz.colors import square_distance, COLOR_THRESHOLD
from parse_qwantz.pixels import normalize_color

logger = logging.getLogger()

DIM = (735, 500)

MASK_FILE_PATH = files(parse_qwantz).joinpath('img/mask.png')

SAMPLE = [
    ((113, 183), (128, 255, 64)),
    ((290, 160), (255, 128, 161)),
    ((704, 183), (255, 242, 179)),
    ((143, 375), (255, 191, 82)),
    ((452, 405), (255, 191, 82)),
    ((585, 386), (69, 196, 5)),
]


class ImageError(Exception):
    pass


@cache
def get_mask_image() -> Image:
    with as_file(MASK_FILE_PATH) as image_path:
        return Image.open(image_path)


def prepare_image(image: Image) -> tuple[Image, list[int]]:
    if image.size != DIM:
        logger.error(f"Wrong image dimensions: {image.size}, only {DIM} is valid")
        raise ImageError(f"Wrong image dimensions: {image.size}, only {DIM} is valid")
    palette = image.getpalette()
    palette = tuple(palette) if palette else None
    good_panels: list[int] = []
    for panel_no, (pixel, expected_color) in enumerate(SAMPLE, start=1):
        color = image.getpixel(pixel)
        color = normalize_color(color, palette)
        if square_distance(color, expected_color) <= COLOR_THRESHOLD:
            good_panels.append(panel_no)
        else:
            logger.info(f"Invalid template: expected {expected_color} at {pixel}; found {color}")
    if not good_panels:
        logger.error("Invalid template")
        raise ImageError(f"Invalid template")
    all_white = Image.new(mode='RGB', size=DIM, color=(255, 255, 255))
    return Image.composite(image, all_white, get_mask_image()), good_panels
