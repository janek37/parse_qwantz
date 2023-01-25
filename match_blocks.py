from typing import Iterable

from text_blocks import TextBlock
from match_lines import Target, Character
from text_lines import TextLine

Character_s = Character | tuple[Character, Character]


def match_blocks(
    line_matches: Iterable[tuple[Target, Target]], text_blocks: list[TextBlock]
) -> tuple[dict[int, Character_s], list[TextBlock]]:
    block_matches: dict[int, tuple[Character_s, TextLine]] = {}
    blocks_by_line: dict[int, TextBlock] = {id(line): block for block in text_blocks for line in block.lines}
    blocks_by_id: dict[int, TextBlock] = {id(block): block for block in text_blocks}
    neighbors: list[tuple[TextLine, TextLine]] = []
    for target1, target2 in line_matches:
        if isinstance(target1, TextLine) and isinstance(target2, TextLine):
            neighbors.append((target1, target2))
        else:
            character, line = (target1, target2) if isinstance(target1, Character) else (target2, target1)
            block = blocks_by_line[id(line)]
            if id(block) not in block_matches:
                block_matches[id(block)] = (character, line)
            else:
                prev_character, prev_line = block_matches[id(block)]
                if prev_line == line:
                    block_matches[id(block)] = ((prev_character, character), line)
                else:
                    block1, block2 = block.split(prev_line, line)
                    del blocks_by_id[id(block)]
                    blocks_by_id[id(block1)] = block1
                    blocks_by_id[id(block2)] = block2
                    for b1line in block1.lines:
                        blocks_by_line[id(b1line)] = block1
                    for b2line in block2.lines:
                        blocks_by_line[id(b2line)] = block2
                    del block_matches[id(block)]
                    block_matches[id(block1)] = (prev_character, prev_line)
                    block_matches[id(block2)] = (character, line)
    while neighbors:
        neighbors_left = []
        for line1, line2 in neighbors:
            if blocks_by_line[id(line1)] == blocks_by_line[id(line2)]:
                block = blocks_by_line[id(line1)]
                block1, block2 = block.split(line1, line2)
                blocks_by_id[id(block1)] = block1
                blocks_by_id[id(block2)] = block2
                for b1line in block1.lines:
                    blocks_by_line[id(b1line)] = block1
                for b2line in block2.lines:
                    blocks_by_line[id(b2line)] = block2
                if id(block) in block_matches:
                    character, line = block_matches[id(block)]
                    del block_matches[id(block)]
                    block_matches[id(block1)] = (character, line)
                    block_matches[id(block2)] = (character, line)
            else:
                block1 = blocks_by_line[id(line1)]
                block2 = blocks_by_line[id(line2)]
            if id(block1) in block_matches:
                block_matches[id(block2)] = block_matches[id(block1)]
            elif id(block2) in block_matches:
                block_matches[id(block1)] = block_matches[id(block2)]
            else:
                neighbors_left.append((line1, line2))
        neighbors = neighbors_left
    final_block_matches = {block_id: character for block_id, (character, line) in block_matches.items()}
    text_block_ids = set(id(block) for block in blocks_by_line.values())
    text_blocks = [blocks_by_id[block_id] for block_id in text_block_ids]
    return final_block_matches, text_blocks
