from typing import Iterable

from box import Box
from detect_blocks import TextBlock
from match_lines import Character


def match_thought(
    thoughts: list[Box], blocks: list[TextBlock], characters: list[Character]
) -> Iterable[tuple[TextBlock, Character]]:
    for block in blocks:
        if any(thought.contains(block.box) for thought in thoughts):
            character = min(characters, key=lambda ch: block.box.distance_squared(ch.box))
            yield block, character
