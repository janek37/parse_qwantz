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
    boxes = get_boxes(text_blocks, characters, inner_padding=-1, outer_padding=3)
    line_candidates = [(line,) + match_line(line, boxes, image) for line in lines]
    block_mapping = {text_line: block for block in text_blocks for text_line in block.lines}
    return CandidateResolver(line_candidates, block_mapping).resolve()


def get_boxes(
    text_blocks: list[TextBlock], characters: list[Character], inner_padding: int, outer_padding: int
) -> list[tuple[Box, Box, Target]]:
    boxes: list[tuple[Box, Box, Target]] = [
        (text_line.box(inner_padding), text_line.box(outer_padding), text_line)
        for text_block in text_blocks
        for text_line in text_block.lines
    ]
    boxes.extend((character.box, character.box, character) for character in characters)
    return boxes


def match_line(
    line: Line, boxes: list[tuple[Box, Box, Target]], image: SimpleImage
) -> tuple[list[Target], list[Target]]:
    candidates: list[list[Target]] = [[], []]
    for i, end in enumerate(line):
        if image.is_on_edge(end):
            candidates[i] = [OFF_PANEL]
    boxes_distances = [
        (inner_box, target, relative_distance_to_box(line, outer_box))
        for inner_box, outer_box, target in boxes
    ]
    aligned_boxes = [
        sorted((-t, inner_box, target) for inner_box, target, t in boxes_distances if t is not None and t <= 0),
        sorted((t, inner_box, target) for inner_box, target, t in boxes_distances if t is not None and t > 0),
    ]
    for i, sorted_boxes in enumerate(aligned_boxes):
        for _t, inner_box, target in sorted_boxes:
            candidates[i].append(target)
            if relative_distance_to_box(line, inner_box) is not None:
                break
    if candidates.count([]) == 1:
        for i in range(2):
            if not candidates[i] and any(isinstance(c, TextLine) for c in candidates[1-i]):
                distance = image.distance_to_edge(line[i])
                logger.warning(f"Unmatched line {line}, assuming off-panel (distance to edge: {distance})")
                candidates[i] = [OFF_PANEL]
    return candidates[0], candidates[1]


def relative_distance_to_box(line: Line, box: Box) -> float | None:
    distances = (
        relative_distance_to_intersection(line, side)
        for side in sides(box)
        if intersects(line, side)
    )
    distances = list(distances)
    return min(distances, default=None, key=abs)


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


class CandidateResolver:
    def __init__(
        self,
        line_candidates: list[tuple[Line, list[Target], list[Target]]],
        block_mapping: dict[TextLine, TextBlock],
    ):
        self.line_candidates = line_candidates
        self.block_mapping = block_mapping
        self.matched_blocks: set[TextBlock] = set()

    def resolve(self) -> tuple[list[tuple[Target, Target]], list[Line]]:
        choices: list[tuple[Target, Target]] = []
        unmatched_lines: list[Line] = []
        for line, candidates1, candidates2 in self.line_candidates:
            if self.is_simple_case(candidates1) and isinstance(candidates1[0], TextLine):
                self.update_matched_blocks(candidates1[0])
            if self.is_simple_case(candidates2) and isinstance(candidates2[0], TextLine):
                self.update_matched_blocks(candidates2[0])
        for line, candidates1, candidates2 in self.line_candidates:
            result = self.first_pass(candidates1, candidates2, line)
            if result == 'unmatched':
                unmatched_lines.append(line)
            elif result == 'simple case':
                choices.append((candidates1[0], candidates2[0]))
            else:
                choices.append(self.second_pass((candidates1, candidates2)))
        return choices, unmatched_lines

    def first_pass(
        self,
        candidates1: list[Target],
        candidates2: list[Target],
        line: Line,
    ) -> str:
        if len(candidates1) == len(candidates2) == 1 and candidates1 == candidates2:
            logger.warning(f"Unmatched line {line}: matches the same object: {candidates1[0]}")
            return 'unmatched'
        elif not (candidates1 and candidates2):
            logger.warning(f"Unmatched line {line}: matches nothing ({candidates1}, {candidates2})")
            return 'unmatched'
        elif not (
                any(isinstance(c, TextLine) for c in candidates1)
                or any(isinstance(c, TextLine) for c in candidates2)
        ):
            logger.warning(f"Unmatched line {line}: matches {candidates1} to {candidates2}")
            return 'unmatched'
        elif self.is_simple_case(candidates1) and self.is_simple_case(candidates2):
            return 'simple case'
        else:
            logger.info(f"Candidates left to resolve: {candidates1}, {candidates2}")
            return 'complex case'

    def second_pass(self, candidates_pair) -> tuple[Target, Target]:
        has_character = [any(isinstance(c, Character) for c in candidates) for candidates in candidates_pair]
        has_textline = [any(isinstance(c, TextLine) for c in candidates) for candidates in candidates_pair]
        has_unmatched_blocks = [
            any(isinstance(c, TextLine) and self.block_mapping[c] not in self.matched_blocks for c in candidates)
            for candidates in candidates_pair
        ]
        if not has_textline[0]:
            prefer = [Character, TextLine]
        elif not has_textline[1]:
            prefer = [TextLine, Character]
        elif not has_character[0]:
            prefer = [TextLine, Character]
        elif not has_character[1]:
            prefer = [Character, TextLine]
        else:
            # both types on both ends
            logger.warning(f"Ambiguous line match candidates: {candidates_pair}")
            if not has_unmatched_blocks[0]:
                prefer = [Character, TextLine]
            elif not has_unmatched_blocks[1]:
                prefer = [TextLine, Character]
            else:
                # both types on both ends, both have unmatched blocks
                prefer = [TextLine, Character]
        choice = [
            self.select_candidate(candidates, preferred_type == Character)
            for candidates, preferred_type in zip(candidates_pair, prefer)
        ]
        for target in choice:
            if isinstance(target, TextLine):
                self.update_matched_blocks(target)
        return choice[0], choice[1]

    def update_matched_blocks(self, text_line: TextLine) -> None:
        self.matched_blocks.add(self.block_mapping[text_line])

    def is_simple_case(self, candidates: list[Target]) -> bool:
        if len(candidates) == 1:
            return True
        if all(isinstance(c, TextLine) for c in candidates):
            block_count = len(set(self.block_mapping[c] for c in candidates))
            if block_count == 1:
                return True
        return False

    def select_candidate(
        self,
        candidates: list[Target],
        prefer_character: bool,
    ) -> Target:
        if prefer_character:
            characters = [c for c in candidates if isinstance(c, Character)]
            if characters:
                return characters[0]
        text_lines = [c for c in candidates if isinstance(c, TextLine)]
        unmatched_lines = [tl for tl in text_lines if self.block_mapping[tl] not in self.matched_blocks]
        if unmatched_lines:
            return unmatched_lines[0]
        if text_lines:
            return text_lines[0]
        return candidates[0]
