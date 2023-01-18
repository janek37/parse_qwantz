import os
from pathlib import Path

import pytest

from parse_qwantz import main

INPUT_FILE_DIR = Path('test/comics')
EXPECTED_OUTPUT_DIR = Path('test/expected_outputs')


@pytest.mark.parametrize('input_file_name', sorted(os.listdir(INPUT_FILE_DIR)))
def test_output(capsys, input_file_name: str):
    main(str(INPUT_FILE_DIR / input_file_name))
    captured = capsys.readouterr()
    expected_output = open(EXPECTED_OUTPUT_DIR / (input_file_name.split('.')[0] + '.txt')).read()
    assert captured.out == expected_output
    assert captured.err == ""
