import logging
from functools import cache
from importlib.resources import as_file, files

from PIL import Image, ImageOps

import parse_qwantz
from parse_qwantz.colors import square_distance, COLOR_THRESHOLD, Color
from parse_qwantz.pixels import normalize_color

logger = logging.getLogger()

DIM = (735, 500)

MASK_FILE_PATH = files(parse_qwantz).joinpath('img/mask.png')

SAMPLE = [
    ((113, 183), (128, 255, 64)),
    ((704, 183), (255, 242, 179)),
    ((452, 405), (255, 191, 82)),
    ((290, 160), (255, 128, 161)),
    ((372, 484), (0, 0, 0)),
]


class ImageError(Exception):
    pass


@cache
def get_mask_image():
    with as_file(MASK_FILE_PATH) as image_path:
        return Image.open(image_path)


def prepare_image(image: Image):
    if image.size != DIM:
        logger.error(f"Wrong image dimensions: {image.size}, only {DIM} is valid")
        raise ImageError(f"Wrong image dimensions: {image.size}, only {DIM} is valid")
    palette = image.getpalette()
    palette = tuple(palette) if palette else None
    corner = Color.get_with_threshold(normalize_color(image.getpixel((2, 2)), palette))
    if corner == Color.WHITE:
        # there's one-pixel shift in three comics: #3479, #3636, #3787
        cropped = image.crop((0, 0, DIM[0] - 1, DIM[1]))
        image = ImageOps.pad(cropped, DIM, color="black", centering=(1, 0))
    for pixel, expected_color in SAMPLE:
        color = image.getpixel(pixel)
        color = normalize_color(color, palette)
        if square_distance(color, expected_color) > COLOR_THRESHOLD:
            logger.error(f"Invalid template: expected {expected_color} at {pixel}; found {color}")
            raise ImageError(f"Invalid template: expected {expected_color} at {pixel}; found {color}")
    all_white = Image.new(mode='RGB', size=DIM, color=(255, 255, 255))
    return Image.composite(image, all_white, get_mask_image())
