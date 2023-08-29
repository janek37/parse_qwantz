import logging
from collections.abc import Iterable

from importlib.resources import as_file, files
from itertools import chain

import parse_qwantz

logger = logging.getLogger()


def make_word_set(dict_path: str, extra_words: Iterable[str] = ()) -> frozenset[str]:
    with as_file(files(parse_qwantz).joinpath(dict_path)) as dict_path:
        dict_words = (line.rstrip('\n').lower() for line in open(dict_path))
    return frozenset(chain(dict_words, extra_words))


QWANTZ_WORD_SET = make_word_set('dict/unambiguous-qwantz.txt')


WORD_SET = make_word_set(
    'dict/canadian-english-huge',
    ["utahraptor", "utahraptor's", "dromiceiomimus", "dromiceiomimus's"],
)


def disambiguate_hyphen(part1: str, part2: str):
    if not (part1 and part2):
        return False
    if part1[-1].islower() and part2[0].isupper():
        return True
    if part2[0].isdigit():
        return True
    part1_lower = part1.lower()
    part2_lower = part2.lower()

    no_hyphen = part1_lower + part2_lower in QWANTZ_WORD_SET
    with_hyphen = f"{part1_lower}-{part2_lower}" in QWANTZ_WORD_SET

    if no_hyphen:
        if with_hyphen:
            logger.warning(f"Ambiguous hyphen ({part1}/{part2}); both in Qwantz dict")
        return False
    if with_hyphen:
        return True
    logger.warning(f"Potentially ambiguous hyphen ({part1}/{part2})")

    no_hyphen = part1_lower + part2_lower in WORD_SET
    separate = part1_lower in WORD_SET and part2_lower in WORD_SET
    if no_hyphen == separate:
        logger.info(f"Ambiguous hyphen ({part1}/{part2}); {'both' if no_hyphen else 'none'} in dict")
        return False
    return separate
