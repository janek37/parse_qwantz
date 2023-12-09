import logging
from typing import Iterable

from parse_qwantz.text_blocks import TextBlock
from parse_qwantz.match_lines import Target, Character, OFF_PANEL
from parse_qwantz.text_lines import TextLine

logger = logging.getLogger()

MULTI_OFF_PANEL = Character.from_name("multiple off-panel voices")


def match_blocks(
    line_matches: Iterable[tuple[Target, Target]], text_blocks: list[TextBlock]
) -> tuple[dict[TextBlock, list[Character]], list[TextBlock], list[tuple[TextLine, TextLine]]]:
    block_matches: dict[TextBlock, tuple[list[Character], TextLine]] = {}
    blocks_by_line: dict[TextLine, TextBlock] = {line: block for block in text_blocks for line in block.lines}
    neighbors: list[tuple[TextLine, TextLine]] = []
    for target1, target2 in line_matches:
        if isinstance(target1, TextLine) and isinstance(target2, TextLine):
            neighbors.append((target1, target2))
        else:
            character, line = (target1, target2) if isinstance(target1, Character) else (target2, target1)
            line: TextLine
            block = blocks_by_line[line]
            if block not in block_matches:
                block_matches[block] = ([character], line)
            else:
                prev_characters, prev_line = block_matches[block]
                if not block.can_split(prev_line, line):
                    if len(prev_characters) == 2:
                        logger.warning("More than two characters share a line")
                    if prev_line != line:
                        logger.warning("Shared separate lines")
                    if character == OFF_PANEL and OFF_PANEL in prev_characters:
                        prev_characters.remove(OFF_PANEL)
                        new_characters = prev_characters + [MULTI_OFF_PANEL]
                    elif character == OFF_PANEL and MULTI_OFF_PANEL in prev_characters:
                        new_characters = prev_characters
                    else:
                        new_characters = prev_characters + [character]
                    block_matches[block] = (new_characters, line)
                else:
                    block1, block2, alignment = block.split(prev_line, line)
                    if alignment.no_gap and (alignment.left_aligned or alignment.char_aligned):
                        logger.warning(
                            f"Splitting blocks: [{block1.content()[:12]}], [{block2.content()[:12]}],"
                            f" strength: {alignment.strength}"
                        )
                    for b1line in block1.lines:
                        blocks_by_line[b1line] = block1
                    for b2line in block2.lines:
                        blocks_by_line[b2line] = block2
                    del block_matches[block]
                    block_matches[block1] = (prev_characters, prev_line)
                    block_matches[block2] = ([character], line)
    while neighbors:
        neighbors_left = []
        for line1, line2 in neighbors:
            if blocks_by_line[line1] == blocks_by_line[line2]:
                # no longer happens
                block = blocks_by_line[line1]
                if block.row_index(line1) == block.row_index(line2):
                    logger.warning(f"Line connects two text lines in one row: {line1.content} -- {line2.content}")
                    continue
                block1, block2, _ = block.split(line1, line2)
                logger.warning(
                    f"Splitting blocks from one character: [{block1.content()}], [{block2.content()}]"
                )
                for b1line in block1.lines:
                    blocks_by_line[b1line] = block1
                for b2line in block2.lines:
                    blocks_by_line[b2line] = block2
                if block in block_matches:
                    characters, line = block_matches[block]
                    del block_matches[block]
                    block_matches[block1] = (characters, line)
                    block_matches[block2] = (characters, line)
            else:
                block1 = blocks_by_line[line1]
                block2 = blocks_by_line[line2]
                if (
                    block1.row_index(line1) not in (0, len(block1.rows) - 1)
                    or block2.row_index(line2) not in (0, len(block2.rows) - 1)
                ):
                    if not (line1.content.isupper() and line2.content.isupper() and line1.is_bold and line2.is_bold):
                        logger.warning(f"Matching a non-edge line to another line: {line1.content} -- {line2.content}")
            if block1 in block_matches and block2 in block_matches:
                if block1.start.y < block2.start.y:
                    first_block, second_block = block1, block2
                else:
                    first_block, second_block = block2, block1
                characters, line = block_matches[first_block]
                other_characters, other_line = block_matches[second_block]
                block_matches[second_block] = characters + other_characters, other_line
            elif block1 in block_matches:
                block_matches[block2] = block_matches[block1][0], line2
            elif block2 in block_matches:
                block_matches[block1] = block_matches[block2][0], line1
            else:
                neighbors_left.append((line1, line2))
        if neighbors == neighbors_left:
            logger.warning(f"Unmatched connected text lines: {neighbors}")
            break
        neighbors = neighbors_left
    final_block_matches = {block_id: characters for block_id, (characters, line) in block_matches.items()}
    text_blocks = list(set(blocks_by_line.values()))
    return final_block_matches, text_blocks, neighbors
