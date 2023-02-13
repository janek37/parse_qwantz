from pathlib import Path

import pytest

from parse_qwantz import main

INPUT_FILE_DIR = Path('test/comics')
EXPECTED_OUTPUT_DIR = Path('test/expected_outputs')


@pytest.mark.parametrize(['name', 'input_file_path'], [(path.stem, path) for path in sorted(INPUT_FILE_DIR.iterdir())])
def test_output(capsys, name: str, input_file_path: Path):
    main(input_file_path)
    captured = capsys.readouterr()
    expected_output = open(EXPECTED_OUTPUT_DIR / (input_file_path.stem + '.txt')).read()
    assert captured.out == expected_output
