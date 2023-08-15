from typing import Iterable

from parse_qwantz.box import Box
from parse_qwantz.text_blocks import TextBlock
from parse_qwantz.match_lines import Character


def match_thought(thoughts: list[Box], blocks: list[TextBlock]) -> Iterable[TextBlock]:
    for block in blocks:
        if sum(
            1 for thought in thoughts if thought.with_margin(block.font.space_width, 0).contains(block.box)
        ) == 1:
            yield block
