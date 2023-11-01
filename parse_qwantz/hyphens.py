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


QWANTZ_WORD_SET = (
    make_word_set('dict/unambiguous-qwantz.txt')
    | make_word_set('dict/html-words.txt')
    | make_word_set('dict/manual-additions.txt')
) - make_word_set('dict/manual-removed.txt')


def disambiguate_hyphen(part1: list[str], part2: list[str]):
    word1 = part1[-1]
    word2 = part2[0]
    if not (word1 and word2):
        return False
    if word1[-1].islower() and word2[0].isupper():
        return True
    if word2[0].isdigit():
        return True
    word1_lower = word1.lower()
    word2_lower = word2.lower()

    no_hyphen = word1_lower + word2_lower in QWANTZ_WORD_SET
    with_hyphen = f"{word1_lower}-{word2_lower}" in QWANTZ_WORD_SET
    all_with_hyphen = f"{'-'.join(part1)}-{'-'.join(part2)}" in QWANTZ_WORD_SET

    parts_for_logging = f"{'-'.join(part1)}/{'-'.join(part2)}"
    if no_hyphen:
        if with_hyphen or all_with_hyphen:
            logger.warning(f"Ambiguous hyphen ({parts_for_logging}); both in Qwantz dict")
        return False
    if with_hyphen or all_with_hyphen:
        return True
    if len(part1) > 1 or len(part2) > 1:
        if word1_lower not in QWANTZ_WORD_SET or word2_lower not in QWANTZ_WORD_SET:
            logger.warning(f"Unexpected hyphenation in multi-hyphened phrase ({parts_for_logging})")
        return True
    logger.warning(f"Unresolved hyphen ({parts_for_logging})")
    return False
