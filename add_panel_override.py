#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

import typer
from PIL import Image

app = typer.Typer()


def add_panel_override(image_path: Path, panel_no: list[int]) -> None:
    overrides = json.load(open('parse_qwantz/data/panel_overrides.json'))
    md5 = hashlib.md5(Image.open(image_path).tobytes()).hexdigest()
    if md5 not in overrides:
        comic_id, file_name = image_path.name.split(' - ')
        overrides[md5] = {"comic_id": int(comic_id), "file_name": file_name, "panels": {}}
    for n in panel_no:
        overrides[md5]["panels"][n] = ["", ""]
    json.dump(overrides, open('parse_qwantz/data/panel_overrides.json', 'w'), indent=2, ensure_ascii=False)


if __name__ == '__main__':
    typer.run(add_panel_override)
