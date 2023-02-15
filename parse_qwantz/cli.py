import logging
from pathlib import Path

import typer

from parse_qwantz.main import main
from parse_qwantz.prepare_image import ImageError

logger = logging.getLogger()

app = typer.Typer()


@app.command()
def cli(
    input_paths: list[Path] = typer.Argument(..., help="Paths to one or more image and/or directory", exists=True),
    output_dir: Path = typer.Option(None, help="Path to the output directory", exists=True, file_okay=False),
    log_level: str = typer.Option('WARNING', help="Log level"),
    debug: bool = typer.Option(False, help="Enable debug features."),
    show_boxes: bool = typer.Option(False, help="Show character boxes (for debug)")
):
    """Generate transcripts for Ryan North's Dinosaur Comics from https://qwantz.com"""
    logger.setLevel(getattr(logging, log_level.upper()))
    for input_path in input_paths:
        if input_path.is_dir():
            image_paths = (child_path for child_path in input_path.iterdir() if child_path.is_file())
        else:
            image_paths = [input_path]
        for image_path in image_paths:
            try:
                main(image_path, output_dir=output_dir, debug=debug, show_boxes=show_boxes)
            except ImageError:
                pass


if __name__ == '__main__':
    app()
