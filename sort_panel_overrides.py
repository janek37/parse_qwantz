#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

import typer
from PIL import Image

app = typer.Typer()


def sort_panel_overrides() -> None:
    overrides = json.load(open('parse_qwantz/data/panel_overrides.json'))
    sorted_overrides = {key: value for key, value in sorted(overrides.items(), key=lambda r: r[1]["comic_id"])}
    json.dump(sorted_overrides, open('parse_qwantz/data/panel_overrides.json', 'w'), indent=2, ensure_ascii=False)


if __name__ == '__main__':
    typer.run(sort_panel_overrides)
