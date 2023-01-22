from typing import NamedTuple

from pixels import Pixel


class Box(NamedTuple):
    top_left: Pixel
    bottom_right: Pixel

    @property
    def top_right(self):
        return Pixel(self.bottom_right.x, self.top_left.y)

    @property
    def bottom_left(self):
        return Pixel(self.top_left.x, self.bottom_right.y)

    @property
    def left(self):
        return self.top_left.x

    @property
    def right(self):
        return self.bottom_right.x

    @property
    def top(self):
        return self.top_left.y

    @property
    def bottom(self):
        return self.bottom_right.y

    def includes(self, pixel: Pixel):
        return self.left <= pixel.x < self.right and self.top <= pixel.y < self.bottom
