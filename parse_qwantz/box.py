import math
from typing import NamedTuple

from parse_qwantz.pixels import Pixel


class Box(NamedTuple):
    top_left: Pixel
    bottom_right: Pixel

    @property
    def top_right(self) -> Pixel:
        return Pixel(self.bottom_right.x, self.top_left.y)

    @property
    def bottom_left(self) -> Pixel:
        return Pixel(self.top_left.x, self.bottom_right.y)

    @property
    def left(self) -> int:
        return self.top_left.x

    @property
    def right(self) -> int:
        return self.bottom_right.x

    @property
    def top(self) -> int:
        return self.top_left.y

    @property
    def bottom(self) -> int:
        return self.bottom_right.y

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    def includes(self, pixel: Pixel) -> bool:
        return self.left <= pixel.x < self.right and self.top <= pixel.y < self.bottom

    def contains(self, box: "Box") -> bool:
        return self.includes(box.top_left) and self.includes(box.bottom_right)

    def distance_squared(self, box: "Box") -> int:
        return (
            get_interval_distance((self.left, self.right), (box.left, box.right))**2
            + get_interval_distance((self.top, self.bottom), (box.top, box.bottom))**2
        )

    def distance(self, pixel: Pixel) -> float:
        if self.includes(pixel):
            return 0
        if self.left <= pixel.x < self.right:
            if pixel.y < self.top:
                return self.top - pixel.y
            else:
                return pixel.y - self.bottom + 1
        if self.top <= pixel.y < self.bottom:
            if pixel.x < self.left:
                return self.left - pixel.x
            else:
                return pixel.x - self.right + 1
        if pixel.x >= self.right and pixel.y >= self.bottom:
            return get_distance(pixel, self.bottom_right)
        if pixel.x >= self.right and pixel.y < self.top:
            return get_distance(pixel, self.top_right)
        if pixel.x < self.left and pixel.y >= self.bottom:
            return get_distance(pixel, self.bottom_left)
        if pixel.x < self.left and pixel.y < self.top:
            return get_distance(pixel, self.top_left)
        assert False

    def with_margin(self, margin_x: int, margin_y: int):
        return Box(
            Pixel(self.left - margin_x, self.top - margin_y),
            Pixel(self.right + margin_x, self.bottom + margin_y),
        )

    @classmethod
    def dummy(cls) -> "Box":
        return cls(Pixel(0, 0), Pixel(0, 0))


def get_interval_distance(interval1: tuple[int, int], interval2: tuple[int, int]) -> int:
    i1, i2 = sorted((interval1, interval2))
    return max(0, i2[0] - i1[1])


def get_distance(p1: Pixel, p2: Pixel) -> float:
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)
