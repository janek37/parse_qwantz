from pathlib import Path

import typer

from parse_qwantz.main import main

app = typer.Typer()


@app.command()
def cli(
    image_path: Path,
    debug: bool = typer.Option(False, help="Enable debug features."),
    show_boxes: bool = typer.Option(False, help="Show character boxes (for debug)")
):
    """Generate transcripts for Ryan North's Dinosaur Comics from https://qwantz.com"""
    main(image_path, debug=debug, show_boxes=show_boxes)


if __name__ == '__main__':
    app()
