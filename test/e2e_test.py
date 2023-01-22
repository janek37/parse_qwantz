import os
from pathlib import Path

import pytest

from parse_qwantz import main

INPUT_FILE_DIR = Path('test/comics')
EXPECTED_OUTPUT_DIR = Path('test/expected_outputs')


@pytest.mark.parametrize('input_file_path', sorted(INPUT_FILE_DIR.iterdir()))
def test_output(capsys, input_file_path: Path):
    main(str(input_file_path))
    captured = capsys.readouterr()
    expected_output = open(EXPECTED_OUTPUT_DIR / (input_file_path.stem + '.txt')).read()
    assert captured.out == expected_output
