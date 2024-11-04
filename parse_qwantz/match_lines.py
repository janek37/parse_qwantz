import itertools
import logging
import math
from dataclasses import dataclass
from enum import Enum
from functools import cmp_to_key

from parse_qwantz.box import Box
from parse_qwantz.lines import Line
from parse_qwantz.text_blocks import TextBlock
from parse_qwantz.pixels import Pixel
from parse_qwantz.simple_image import SimpleImage
from parse_qwantz.text_lines import TextLine

logger = logging.getLogger()


class Direction(Enum):
    LEFT = "left"
    RIGHT = "right"


@dataclass(frozen=True, eq=True)
class Character:
    name: str
    boxes: tuple[Box, ...]
    direction: Direction | None = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"Character(name={self.name})"

    @classmethod
    def from_name(cls, name: str):
        return cls(name, ())


OFF_PANEL = Character.from_name("off panel")

Target = TextLine | Character

CHARACTER_DISTANCE_THRESHOLD = 35
TEXT_LINE_DISTANCE_THRESHOLD = 44
MISS_ANGLE_COS_THRESHOLD = 0.5
TEXT_LINE_INNER_PADDING = -1
HORIZONTAL_LINE_THRESHOLD = 2.3


@dataclass(frozen=True, eq=True)
class AnnotatedTarget:
    target: Target
    distance: float
    miss_angle_cos: float
    line: Line | None = None
    end_no: int | None = None

    def __repr__(self):
        return f"AnnotatedTarget({repr(self.target)}, dist={self.distance:.2f}, cos={self.miss_angle_cos:.2f})"

    @classmethod
    def from_text_line(cls, text_line: TextLine, line: Line, end_no: int):
        box = text_line.base_box(TEXT_LINE_INNER_PADDING)
        return cls(
            target=text_line,
            distance=get_box_distance(box, line, end_no),
            miss_angle_cos=get_miss_angle_cos(box, line, end_no),
            line=line,
            end_no=end_no,
        )

    @classmethod
    def from_character(cls, character: Character, line: Line, end_no: int):
        distances = (get_box_distance(box, line, end_no) for box in character.boxes)
        distance = min((distance for distance in distances if distance is not None), default=None)
        miss_angle_cos = max(get_miss_angle_cos(box, line, end_no) for box in character.boxes)
        return cls(target=character, distance=distance, miss_angle_cos=miss_angle_cos, line=line, end_no=end_no)


def match_lines(
    lines: list[Line], text_blocks: list[TextBlock], characters: list[Character], image: SimpleImage
) -> tuple[list[tuple[Target, Target]], list[Line]]:
    text_lines = [text_line for text_block in text_blocks for text_line in text_block.lines]
    line_candidates = [(line,) + match_line(line, text_lines, characters, image) for line in lines]
    # for _line, left, right in line_candidates:
    #     logger.info('candidates:')
    #     logger.info('left: ' + ' | '.join(str(l) for l in left))
    #     logger.info('right: ' + ' | '.join(str(r) for r in right))
    block_mapping = {text_line: block for block in text_blocks for text_line in block.lines}
    return CandidateResolver(line_candidates, block_mapping).resolve()


def match_line(
    line: Line, text_lines: list[TextLine], characters: list[Character], image: SimpleImage
) -> tuple[list[AnnotatedTarget], list[AnnotatedTarget]]:
    candidates: list[list[AnnotatedTarget]] = [[], []]
    for i, end in enumerate(line):
        if image.is_on_edge(end):
            candidates[i] = [AnnotatedTarget(OFF_PANEL, 0, 0)]
        else:
            annotated_targets = [
                AnnotatedTarget.from_text_line(text_line, line, i)
                for text_line in text_lines
            ] + [
                AnnotatedTarget.from_character(character, line, i)
                for character in characters
            ]
            filtered_targets = (
                at
                for at in annotated_targets
                if (
                    at.distance is not None
                    and at.miss_angle_cos > MISS_ANGLE_COS_THRESHOLD
                    and not (isinstance(at.target, Character) and at.miss_angle_cos < 1)
                    and not (isinstance(at.target, Character) and at.distance > CHARACTER_DISTANCE_THRESHOLD)
                    and not (isinstance(at.target, TextLine) and at.distance > TEXT_LINE_DISTANCE_THRESHOLD)
                )
            )
            candidates[i] = sorted(filtered_targets, key=lambda at: at.distance)
    return candidates[0], candidates[1]


def get_box_distance(box: Box, line: Line, end_no: int) -> float | None:
    distance = box.distance(line[end_no])
    if distance is None:
        return None
    other_end = line[1 - end_no]
    other_distance = box.distance(other_end)
    if other_distance is not None and distance > other_distance:
        return None
    return distance


def get_miss_angle_cos(box: Box, line: Line, end_no: int) -> float:
    corners = [box.top_left, box.bottom_left, box.top_right, box.bottom_right]
    angle_cosines = [get_angle_cos(line, end_no, corner) for corner in corners]
    max_angle_cos = max(angle_cosines)
    if max_angle_cos < 0:
        return max_angle_cos
    if any(intersects(line, end_no, side) for side in sides(box)):
        return 1
    return max_angle_cos


def sides(box: Box) -> list[Line]:
    return [
        (box.top_left, box.bottom_left),
        (box.bottom_left, box.bottom_right),
        (box.bottom_right, box.top_right),
        (box.top_right, box.top_left),
    ]


def intersects(line: Line, end_no: int, segment: Line) -> bool:
    if end_no == 1:
        (x0, y0), (x1, y1) = line
    else:
        (x1, y1), (x0, y0) = line
    (ax, ay), (bx, by) = segment
    if ((y0 - y1)*(ax - x0) + (x1 - x0)*(ay - y0)) * ((y0 - y1)*(bx - x0) + (x1 - x0)*(by - y0)) > 0:
        return False
    # (x0, y0) + t (x1 - x0, y1 - y0)
    # -> for which t is it on the ab line?
    denominator = (x1 - x0)*(by - ay) - (y1 - y0)*(bx - ax)
    if denominator == 0:
        return True
    t = ((ax - x0)*(by - ay) - (ay - y0)*(bx - ax)) / denominator
    return t > 1


def get_angle_cos(line: Line, end_no: int, pixel: Pixel) -> float:
    this_end = line[end_no]
    other_end = line[1-end_no]
    vec1 = (this_end[0] - other_end[0], this_end[1] - other_end[1])
    vec2 = (pixel[0] - this_end[0], pixel[1] - this_end[1])
    dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1]
    abs1 = math.sqrt(vec1[0]*vec1[0] + vec1[1]*vec1[1])
    abs2 = math.sqrt(vec2[0]*vec2[0] + vec2[1]*vec2[1])
    denominator = abs1 * abs2
    return 1 if denominator < 0.00001 else dot_product/denominator


class CandidateResolver:
    def __init__(
        self,
        line_candidates: list[tuple[Line, list[AnnotatedTarget], list[AnnotatedTarget]]],
        block_mapping: dict[TextLine, TextBlock],
    ):
        self.line_candidates = line_candidates
        self.block_mapping = block_mapping
        self.matched_blocks: set[TextBlock] = set()

    def resolve(self) -> tuple[list[tuple[Target, Target]], list[Line]]:
        unmatched_lines: list[Line] = []
        updated_candidates: list[tuple[list[AnnotatedTarget], list[AnnotatedTarget]]] = []
        for line, candidates1, candidates2 in self.line_candidates:
            if self.is_line_matched(candidates1, candidates2, line):
                updated_candidates.append((candidates1, candidates2))
            else:
                unmatched_lines.append(line)
        while not self.is_all_resolved(updated_candidates):
            changed, updated_candidates = self.resolve_candidates(updated_candidates)
            if not changed:
                for candidates1, candidates2 in updated_candidates:
                    if len(candidates1) > 1 or len(candidates2) > 1:
                        logger.warning(f"Candidates not fully resolved: {candidates1}, {candidates2}")
                updated_candidates = self.force_resolve_candidates(updated_candidates)
                break
        choices = [(candidates1[0].target, candidates2[0].target) for candidates1, candidates2 in updated_candidates]
        return choices, unmatched_lines

    def resolve_candidates(
        self, candidates_pairs: list[tuple[list[AnnotatedTarget], list[AnnotatedTarget]]]
    ) -> tuple[bool, list[tuple[list[AnnotatedTarget], list[AnnotatedTarget]]]]:
        updated_candidates_pairs = []
        changed = False
        for candidates1, candidates2 in candidates_pairs:
            best_candidates1 = self.best_candidates(candidates1, candidates2)
            best_candidates2 = self.best_candidates(candidates2, best_candidates1)
            if len(best_candidates1) < len(candidates1) or len(best_candidates2) < len(candidates2):
                changed = True
            updated_candidates_pairs.append((best_candidates1, best_candidates2))
            for best_candidates in (best_candidates1, best_candidates2):
                if len(best_candidates) == 1 and isinstance(best_candidates[0].target, TextLine):
                    if self.update_matched_blocks(best_candidates[0].target):
                        changed = True
        return changed, updated_candidates_pairs

    def force_resolve_candidates(
        self, candidates_pairs: list[tuple[list[AnnotatedTarget], list[AnnotatedTarget]]]
    ) -> list[tuple[list[AnnotatedTarget], list[AnnotatedTarget]]]:
        updated_candidates_pairs = []
        for candidates1, candidates2 in candidates_pairs:
            if len(candidates1) == 1 and len(candidates2) == 1:
                updated_candidates_pairs.append((candidates1, candidates2))
            else:
                product = itertools.product([TextLine, Character], [candidates1, candidates2])
                if all(any(isinstance(c.target, klass) for c in candidates) for klass, candidates in product):
                    variant1 = (
                        self.best_candidates_for_other_end(candidates1, other_end_is_character=True),
                        self.best_candidates_for_other_end(candidates2, other_end_is_character=False),
                    )
                    variant2 = (
                        self.best_candidates_for_other_end(candidates1, other_end_is_character=False),
                        self.best_candidates_for_other_end(candidates2, other_end_is_character=True),
                    )
                    updated_candidates_pairs.append(
                        variant1 if self.rate_variant(variant1) > self.rate_variant(variant2) else variant2
                    )
                else:
                    horizontal1, horizontal2 = [
                        [c for c in candidates if isinstance(c.target, TextLine) and self.is_horizontal_match(c)]
                        for candidates in (candidates1, candidates2)
                    ]
                    candidates1 = horizontal1 or candidates1
                    candidates2 = horizontal2 or candidates2
                    closest1 = min(candidates1, key=lambda c: c.distance)
                    closest2 = min(candidates2, key=lambda c: c.distance)
                    updated_candidates_pairs.append(([closest1], [closest2]))
        return updated_candidates_pairs

    def rate_variant(self, variant: tuple[list[AnnotatedTarget], list[AnnotatedTarget]]) -> tuple[bool, float]:
        side1, side2 = variant
        unmatched = True
        for annotated_target in side1 + side2:
            if isinstance(annotated_target.target, TextLine) and self.is_text_line_matched(annotated_target.target):
                unmatched = False
                break
        total_distance = min(at.distance for at in side1) + min(at.distance for at in side2)
        return unmatched, -total_distance

    @staticmethod
    def is_all_resolved(candidates_pairs: list[tuple[list[AnnotatedTarget], list[AnnotatedTarget]]]) -> bool:
        for candidates1, candidates2 in candidates_pairs:
            if len(candidates1) > 1 or len(candidates2) > 1:
                return False
        return True

    def best_candidates(
        self, candidates: list[AnnotatedTarget], other_end_candidates: list[AnnotatedTarget]
    ) -> list[AnnotatedTarget]:
        best_candidates = set()
        for other_end_candidate in other_end_candidates:
            new_best_candidates = self.best_candidates_for_other_end(candidates, other_end_candidate)
            best_candidates.update(new_best_candidates)
        best_candidates = sorted(best_candidates, key=lambda c: c.distance)
        if self.is_simple_case(best_candidates):
            return best_candidates[:1]
        else:
            return best_candidates

    def best_candidates_for_other_end(
        self,
        candidates: list[AnnotatedTarget],
        other_end_target: AnnotatedTarget | None = None,
        other_end_is_character: bool = False,
    ) -> list[AnnotatedTarget]:
        sorted_candidates = sorted(
            candidates, key=cmp_to_key(lambda c1, c2: self.compare(c1, c2, other_end_target, other_end_is_character))
        )
        best = [sorted_candidates[0]]
        for c in sorted_candidates[1:]:
            if self.compare(c, sorted_candidates[0], other_end_target, other_end_is_character) == 0:
                best.append(c)
        return best

    def compare(
        self,
        target1: AnnotatedTarget,
        target2: AnnotatedTarget,
        other_end_target: AnnotatedTarget | None = None,
        other_end_is_character: bool = False,
    ) -> int:
        other_end_is_character = (
            other_end_is_character
            or (other_end_target and isinstance(other_end_target.target, Character))
        )
        if isinstance(target1.target, Character) and isinstance(target2.target, Character):
            return -1 if target1.distance < target2.distance else 1
        if isinstance(target1.target, TextLine) and isinstance(target2.target, TextLine):
            tl1, tl2 = target1.target, target2.target
            multiplier1 = 1.15 if target1.miss_angle_cos < 0.95 else 1
            multiplier2 = 1.15 if target2.miss_angle_cos < 0.95 else 1
            if (
                (target1.miss_angle_cos > target2.miss_angle_cos or target1.miss_angle_cos == 1)
                and target1.distance < target2.distance * multiplier2 and not self.is_horizontal_match(target2)
            ):
                return -1
            if (
                (target1.miss_angle_cos < target2.miss_angle_cos or target2.miss_angle_cos == 1)
                and target1.distance * multiplier1 > target2.distance and not self.is_horizontal_match(target1)
            ):
                return 1
            if not self.is_text_line_matched(tl1) and self.is_text_line_matched(tl2):
                return -1
            if self.is_text_line_matched(tl1) and not self.is_text_line_matched(tl2):
                return 1
            if other_end_target is None or other_end_target.target != OFF_PANEL:
                if not self.is_narrator(tl1) and self.is_narrator(tl2):
                    return -1
                if self.is_narrator(tl1) and not self.is_narrator(tl2):
                    return 1
            return 0
        # different types of targets
        ann_text_line, ann_character, choose_text_line, choose_character = (
            (target1, target2, -1, 1) if isinstance(target1.target, TextLine) else (target2, target1, 1, -1)
        )
        if other_end_is_character:
            return choose_text_line
        # other target is text line
        if other_end_target and self.is_godlike(other_end_target.target):
            # prefer not to match godlike text to characters
            if self.is_godlike(ann_text_line.target):
                return choose_text_line
        if ann_character.distance < ann_text_line.distance:
            return choose_character
        # text line is closer
        if ann_text_line.miss_angle_cos == 1:
            return choose_text_line
        return choose_character

    @staticmethod
    def is_horizontal_match(ann_target: AnnotatedTarget) -> bool:
        if ann_target.line:
            line = ann_target.line
            target_box = ann_target.target.box()
            target_top = target_box.top
            target_bottom = target_box.bottom
            horizontal = abs(line[0].x - line[1].x) > HORIZONTAL_LINE_THRESHOLD * abs(line[0].y - line[1].y)
            if target_top < line[ann_target.end_no].y < target_bottom and horizontal:
                return True
        return False

    @staticmethod
    def is_line_matched(
        candidates1: list[AnnotatedTarget],
        candidates2: list[AnnotatedTarget],
        line: Line,
    ) -> bool:
        if len(candidates1) == len(candidates2) == 1 and candidates1[0].target == candidates2[0].target:
            logger.warning(f"Unmatched line {line}: matches the same object: {candidates1[0].target}")
            return False
        elif not (candidates1 and candidates2):
            logger.warning(f"Unmatched line {line}: matches nothing ({candidates1}, {candidates2})")
            return False
        elif not (
            any(isinstance(c.target, TextLine) for c in candidates1)
            or any(isinstance(c.target, TextLine) for c in candidates2)
        ):
            logger.warning(f"Unmatched line {line}: matches {candidates1} to {candidates2}")
            return False
        else:
            return True

    def update_matched_blocks(self, text_line: TextLine) -> bool:
        if self.block_mapping[text_line] not in self.matched_blocks:
            self.matched_blocks.add(self.block_mapping[text_line])
            return True
        return False

    def is_text_line_matched(self, text_line: TextLine) -> bool:
        return self.block_mapping[text_line] in self.matched_blocks

    def is_narrator(self, text_line: TextLine) -> bool:
        block = self.block_mapping[text_line]
        return text_line.is_bold and block.box.top < text_line.font.height

    @staticmethod
    def is_godlike(text_line: TextLine) -> bool:
        return text_line.is_bold and text_line.content.isupper()

    def is_simple_case(self, candidates: list[AnnotatedTarget]) -> bool:
        if len(candidates) == 1:
            return True
        if all(isinstance(c.target, TextLine) for c in candidates):
            block_count = len(set(self.block_mapping[c.target] for c in candidates))
            if block_count == 1:
                return True
        if all(isinstance(c.target, Character) for c in candidates):
            name_count = len(set(c.target.name for c in candidates))
            if name_count == 1:
                return True
        return False
