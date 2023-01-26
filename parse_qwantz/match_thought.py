from typing import Iterable

from parse_qwantz.box import Box
from parse_qwantz.text_blocks import TextBlock
from parse_qwantz.match_lines import Character


def match_thought(
    thoughts: list[Box], blocks: list[TextBlock], characters: list[Character]
) -> Iterable[tuple[TextBlock, Character]]:
    for block in blocks:
        if any(thought.contains(block.box) for thought in thoughts):
            character = min(characters, key=lambda ch: block.box.distance_squared(ch.box))
            yield block, character
