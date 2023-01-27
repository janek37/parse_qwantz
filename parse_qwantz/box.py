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

    @classmethod
    def dummy(cls) -> "Box":
        return cls(Pixel(0, 0), Pixel(0, 0))


def get_interval_distance(interval1: tuple[int, int], interval2: tuple[int, int]) -> int:
    i1, i2 = sorted((interval1, interval2))
    return max(0, i2[0] - i1[1])
