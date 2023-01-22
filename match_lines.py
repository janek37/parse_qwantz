import logging
from dataclasses import dataclass
from typing import Iterable

from box import Box
from detect_lines import Line
from detect_blocks import TextBlock
from pixels import Pixel
from simple_image import SimpleImage

logger = logging.getLogger()


@dataclass
class Character:
    name: str
    box: Box
    can_think: bool = True

    def __str__(self):
        return self.name

    @classmethod
    def from_name(cls, name: str):
        return cls(name, Box(Pixel(0, 0), Pixel(0, 0)))


OFF_PANEL = Character.from_name("Off-Panel")

Target = TextBlock | Character


class UnmatchedLine(Exception):
    pass


def match_lines(
    lines: list[Line], text_blocks: list[TextBlock], characters: list[Character], image: SimpleImage
) -> Iterable[tuple[Target, Target]]:
    boxes: list[tuple[Box, Target]] = [
        (text_line.box(margin=1), text_block)
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
                    t = relative_distance_to_intersection(line, side)
                    if t <= 0 and (distance1 is None or -t < distance1):
                        distance1 = -t
                        closest1 = target
                    elif t > 0 and (distance2 is None or t < distance2):
                        distance2 = t
                        closest2 = target
                    break
        if not (isinstance(closest1, TextBlock) or isinstance(closest2, TextBlock)) or closest1 is closest2 is None:
            logger.error(f"Unmatched line {line}: matches {closest1} to {closest2}")
            raise UnmatchedLine(line, boxes, text_blocks)
        if (closest1 is None and closest2 is None) or (closest1 is not None and closest2 is None):
            logger.warning(f"Unmatched line {line}, assuming off-panel")
            if closest1 is None:
                closest1 = OFF_PANEL
            if closest2 is None:
                closest2 = OFF_PANEL
        if closest1 == closest2:
            logger.error(f"Line {line} matches the same object: {closest1}")
            raise UnmatchedLine(line, boxes, text_blocks)
        yield closest1, closest2


def sides(box: Box) -> list[Line]:
    return [
        (box.top_left, box.bottom_left),
        (box.bottom_left, box.bottom_right),
        (box.bottom_right, box.top_right),
        (box.top_right, box.top_left),
    ]


def intersects(line: Line, segment: Line) -> bool:
    (x0, y0), (x1, y1) = line
    (ax, ay), (bx, by) = segment
    return ((y0 - y1)*(ax - x0) + (x1 - x0)*(ay - y0)) * ((y0 - y1)*(bx - x0) + (x1 - x0)*(by - y0)) < 0


def relative_distance_to_intersection(line: Line, segment: Line) -> float:
    (x0, y0), (x1, y1) = line
    (ax, ay), (bx, by) = segment
    # (x0, y0) + t (x1 - x0, y1 - y0)
    # -> for which t is it on the ab line?
    t = ((ax - x0)*(by - ay) - (ay - y0)*(bx - ax)) / ((x1 - x0)*(by - ay) - (y1 - y0)*(bx - ax))
    if t > 1 or t < 0:
        return t
    else:
        return 0 if is_left(line, segment[0]) else 1


def is_left(line: Line, point: Pixel) -> bool:
    (ax, ay), (bx, by) = line
    cx, cy = point
    return (bx - ax)*(cy - ay) - (by - ay)*(cx - ax) > 0
