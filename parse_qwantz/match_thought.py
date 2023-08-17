from typing import Iterable

from parse_qwantz.box import Box
from parse_qwantz.text_blocks import TextBlock


def match_thought(thoughts: list[Box], blocks: list[TextBlock]) -> Iterable[TextBlock]:
    for block in blocks:
        vertical_margin = block.font.height - block.font.base
        containing_thoughts = (
            thought
            for thought in thoughts
            if thought.with_margin(block.font.space_width, vertical_margin).contains(block.box)
        )
        if sum(1 for _ in containing_thoughts) == 1:
            yield block
