from typing import Iterable

from detect_blocks import TextBlock
from match_lines import Target, Character


def match_blocks(line_matches: Iterable[tuple[Target, Target]]):
    block_matches = {}
    neighbors = []
    for target1, target2 in line_matches:
        if isinstance(target1, TextBlock) and isinstance(target2, TextBlock):
            neighbors.append((target1, target2))
        else:
            character, block = (target1, target2) if isinstance(target1, Character) else (target2, target1)
            block_matches[id(block)] = character
    while neighbors:
        neighbors_left = []
        for block1, block2 in neighbors:
            if id(block1) in block_matches:
                block_matches[id(block2)] = block_matches[id(block1)]
            elif id(block2) in block_matches:
                block_matches[id(block1)] = block_matches[id(block2)]
            else:
                neighbors_left.append((block1, block2))
        neighbors = neighbors_left
    return block_matches
