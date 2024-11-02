import json
from functools import cache
from importlib.resources import files, as_file

import parse_qwantz

OVERRIDE_FILE_PATH = files(parse_qwantz).joinpath('data/panel_overrides.json')


@cache
def get_panel_overrides() -> dict[str, dict[str, list[str]]]:
    with as_file(OVERRIDE_FILE_PATH) as override_path:
        return {
            key: value["panels"]
            for key, value in json.load(open(override_path)).items()
        }
