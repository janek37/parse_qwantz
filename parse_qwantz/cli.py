import logging
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path

import typer
from PIL import ImageShow

from parse_qwantz.image_viewer import SilentViewer
from parse_qwantz.main import main
from parse_qwantz.prepare_image import ImageError

logger = logging.getLogger()

ImageShow.register(SilentViewer(), 0)

app = typer.Typer()


@dataclass
class Inner:
    output_dir: Path | None
    debug: bool
    show_boxes: bool
    unambiguous_words: bool

    def __call__(self, image_path: Path):
        try:
            main(
                image_path,
                output_dir=self.output_dir,
                debug=self.debug,
                show_boxes=self.show_boxes,
                unambiguous_words=self.unambiguous_words,
            )
        except ImageError:
            pass


@app.command()
def cli(
    input_paths: list[Path] = typer.Argument(..., help="Paths to one or more image and/or directory", exists=True),
    output_dir: Path = typer.Option(None, help="Path to the output directory", exists=True, file_okay=False),
    log_level: str = typer.Option('WARNING', help="Log level"),
    debug: bool = typer.Option(False, help="Enable debug features."),
    show_boxes: bool = typer.Option(False, help="Show character boxes (for debug)"),
    unambiguous_words: bool = typer.Option(False, help="Print only unambiguous words"),
):
    """Generate transcripts for Ryan North's Dinosaur Comics from https://qwantz.com"""
    logger.setLevel(getattr(logging, log_level.upper()))
    for input_path in input_paths:
        if input_path.is_dir():
            image_paths = (child_path for child_path in input_path.iterdir() if child_path.is_file())
        else:
            image_paths = [input_path]

        inner = Inner(
            output_dir=output_dir,
            debug=debug,
            show_boxes=show_boxes,
            unambiguous_words=unambiguous_words,
        )

        with Pool(4) as pool:
            pool.map(inner, image_paths)


if __name__ == '__main__':
    app()
