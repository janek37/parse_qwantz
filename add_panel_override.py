#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

import typer
from PIL import Image

from parse_qwantz.parser import parse_qwantz

app = typer.Typer()


def add_panel_override(image_path: Path, comic_id: int, panel_no: list[int]) -> None:
    overrides = json.load(open('parse_qwantz/data/panel_overrides.json'))
    image = Image.open(image_path)
    md5 = hashlib.md5(image.tobytes()).hexdigest()
    if md5 not in overrides:
        file_name = image_path.name
        overrides[md5] = {"comic_id": int(comic_id), "file_name": file_name, "panels": {}}
    panels = list(parse_qwantz(image))
    for n in panel_no:
        overrides[md5]["panels"][n] = panels[n-1]
    json.dump(overrides, open('parse_qwantz/data/panel_overrides.json', 'w'), indent=2, ensure_ascii=False)


if __name__ == '__main__':
    typer.run(add_panel_override)
