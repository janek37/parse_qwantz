from dataclasses import dataclass
from typing import Iterable

from detect_lines import Line
from detect_blocks import TextBlock
from pixels import Pixel, SimpleImage


@dataclass
class Character:
    name: str
    box: tuple[Pixel, Pixel]

    def __str__(self):
        return self.name


OFF_PANEL = Character("Off-Panel", ((0, 0), (0, 0)))

Target = TextBlock | Character


class UnmatchedLine(Exception):
    pass


def match_lines(
    lines: list[Line], text_blocks: list[TextBlock], characters: list[Character], image: SimpleImage
) -> Iterable[tuple[Target, Target]]:
    boxes: list[tuple[tuple[Pixel, Pixel], Target]] = [
        (text_line.box(), text_block)
        for text_block in text_blocks
        for text_line in text_block.lines
    ]
    boxes.extend((character.box, character) for character in characters)
    for line in lines:
        end1, end2 = line
        distance1 = distance2 = None
        closest1 = closest2 = None
        if image.is_on_edge(end1):
            distance1 = 0
            closest1 = OFF_PANEL
        if image.is_on_edge(end2):
            distance2 = 0
            closest2 = OFF_PANEL
        for box, target in boxes:
            for side in sides(box):
                if intersects(line, side):
                    d1 = dist_to_segment_squared(end1, side)
                    d2 = dist_to_segment_squared(end2, side)
                    if d1 < d2 and (distance1 is None or d1 < distance1):
                        distance1 = d1
                        closest1 = target
                    elif d1 >= d2 and (distance2 is None or d2 < distance2):
                        distance2 = d2
                        closest2 = target
                    break
        if (
            closest1 is None
            or closest2 is None
            or not (isinstance(closest1, TextBlock) or isinstance(closest2, TextBlock))
        ):
            raise UnmatchedLine(line)
        if closest1 == closest2:
            raise UnmatchedLine(line)
        yield closest1, closest2


def sides(box: tuple[Pixel, Pixel]) -> list[tuple[Pixel, Pixel]]:
    (x0, y0), (x1, y1) = box
    return [((x0, y0), (x0, y1)), ((x0, y1), (x1, y1)), ((x1, y1), (x1, y0)), ((x1, y0), (x0, y0))]


def intersects(line: Line, segment: Line) -> bool:
    (x0, y0), (x1, y1) = line
    (ax, ay), (bx, by) = segment
    return ((y0 - y1)*(ax - x0) + (x1 - x0)*(ay - y0)) * ((y0 - y1)*(bx - x0) + (x1 - x0)*(by - y0)) < 0


# https://stackoverflow.com/a/1501725/245594
def dist_to_segment_squared(point: Pixel, segment: Line) -> float:
    l2 = dist2(*segment)  # i.e. |w-v|^2
    if l2 == 0:
        return dist2(point, segment[0])
    px, py = point
    (vx, vy), (wx, wy) = segment
    # Consider the line extending the segment, parameterized as v + t (w - v).
    # We find projection of point p onto the line.
    # It falls where t = [(p-v) . (w-v)] / |w-v|^2
    # We clamp t from [0,1] to handle points outside the segment vw.
    t = ((px - vx) * (wx - vx) + (py - vy) * (wy - vy)) / l2
    t = max(0., min(1., t))
    return dist2(point, (vx + t * (wx - vx), vy + t * (wy - vy)))


def dist2(p1: Pixel, p2: tuple[int | float, int | float]) -> int | float:
    return (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2
