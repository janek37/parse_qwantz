from typing import NamedTuple

from pixels import Pixel


class Box(NamedTuple):
    top_left: Pixel
    bottom_right: Pixel
