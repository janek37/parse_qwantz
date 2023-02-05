import logging
from dataclasses import dataclass

from parse_qwantz.box import Box
from parse_qwantz.lines import Line
from parse_qwantz.text_blocks import TextBlock
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage
from parse_qwantz.text_lines import TextLine

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
        return cls(name, Box.dummy())


OFF_PANEL = Character.from_name("Off-Panel")

Target = TextLine | Character


def match_lines(
    lines: list[Line], text_blocks: list[TextBlock], characters: list[Character], image: SimpleImage
) -> tuple[list[tuple[Target, Target]], list[Line]]:
    boxes: list[tuple[Box, Target]] = [
        (text_line.box(padding=1), text_line)
        for text_block in text_blocks
        for text_line in text_block.lines
    ]
    boxes.extend((character.box, character) for character in characters)
    unmatched_lines = []
    matches = []
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
        if (closest1 is None and closest2 is not None) or (closest1 is not None and closest2 is None):
            logger.warning(f"Unmatched line {line}, assuming off-panel")
            if closest1 is None:
                closest1 = OFF_PANEL
            if closest2 is None:
                closest2 = OFF_PANEL
        if closest1 == closest2 and closest1 is not None:
            logger.warning(f"Line {line} matches the same object: {closest1}")
            unmatched_lines.append(line)
        elif not (isinstance(closest1, TextLine) or isinstance(closest2, TextLine)):
            logger.warning(f"Unmatched line {line}: matches {closest1} to {closest2}")
            unmatched_lines.append(line)
        else:
            matches.append((closest1, closest2))
    return matches, unmatched_lines


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
        return -t if is_left(line, segment[0]) else 2 - t


def is_left(line: Line, point: Pixel) -> bool:
    (ax, ay), (bx, by) = line
    cx, cy = point
    return (bx - ax)*(cy - ay) - (by - ay)*(cx - ax) > 0
