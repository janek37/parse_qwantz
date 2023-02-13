import logging
from typing import Iterable

from parse_qwantz.text_blocks import TextBlock
from parse_qwantz.match_lines import Target, Character
from parse_qwantz.text_lines import TextLine

logger = logging.getLogger()

Character_s = Character | tuple[Character, Character]

MatchDict = dict[TextBlock, Character_s]


def match_blocks(
    line_matches: Iterable[tuple[Target, Target]], text_blocks: list[TextBlock]
) -> tuple[MatchDict, list[TextBlock], list[tuple[TextLine, TextLine]]]:
    block_matches: dict[TextBlock, tuple[Character_s, TextLine]] = {}
    blocks_by_line: dict[TextLine, TextBlock] = {line: block for block in text_blocks for line in block.lines}
    neighbors: list[tuple[TextLine, TextLine]] = []
    for target1, target2 in line_matches:
        if isinstance(target1, TextLine) and isinstance(target2, TextLine):
            neighbors.append((target1, target2))
        else:
            character, line = (target1, target2) if isinstance(target1, Character) else (target2, target1)
            block = blocks_by_line[line]
            if block not in block_matches:
                block_matches[block] = (character, line)
            else:
                prev_character, prev_line = block_matches[block]
                if prev_line == line:
                    block_matches[block] = ((prev_character, character), line)
                else:
                    block1, block2 = block.split(prev_line, line)
                    logger.warning(
                        f"Splitting blocks: [{block1.content()}], [{block2.content()}]"
                    )
                    for b1line in block1.lines:
                        blocks_by_line[b1line] = block1
                    for b2line in block2.lines:
                        blocks_by_line[b2line] = block2
                    del block_matches[block]
                    block_matches[block1] = (prev_character, prev_line)
                    block_matches[block2] = (character, line)
    while neighbors:
        neighbors_left = []
        for line1, line2 in neighbors:
            if blocks_by_line[line1] == blocks_by_line[line2]:
                block = blocks_by_line[line1]
                block1, block2 = block.split(line1, line2)
                for b1line in block1.lines:
                    blocks_by_line[b1line] = block1
                for b2line in block2.lines:
                    blocks_by_line[b2line] = block2
                if block in block_matches:
                    character, line = block_matches[block]
                    del block_matches[block]
                    block_matches[block1] = (character, line)
                    block_matches[block2] = (character, line)
            else:
                block1 = blocks_by_line[line1]
                block2 = blocks_by_line[line2]
            if block1 in block_matches:
                block_matches[block2] = block_matches[block1]
            elif block2 in block_matches:
                block_matches[block1] = block_matches[block2]
            else:
                neighbors_left.append((line1, line2))
        if neighbors == neighbors_left:
            logger.warning(f"Unmatched connected text lines: {neighbors}")
            break
        neighbors = neighbors_left
    final_block_matches = {block_id: character for block_id, (character, line) in block_matches.items()}
    text_blocks = list(set(blocks_by_line.values()))
    return final_block_matches, text_blocks, neighbors
