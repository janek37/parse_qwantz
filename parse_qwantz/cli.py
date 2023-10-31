import logging
from dataclasses import dataclass
from multiprocessing import Pool
from pathlib import Path

import typer
from PIL import ImageShow

from parse_qwantz.color_logs import set_logging_formatter
from parse_qwantz.image_viewer import SilentViewer
from parse_qwantz.main import main
from parse_qwantz.prepare_image import ImageError

ImageShow.register(SilentViewer(), 0)

app = typer.Typer()


@dataclass
class Inner:
    output_dir: Path | None
    debug: bool
    show_boxes: bool
    unambiguous_words: bool
    generate_svg: bool
    parse_footer: bool

    def __call__(self, image_path: Path):
        try:
            return main(
                image_path,
                output_dir=self.output_dir,
                debug=self.debug,
                show_boxes=self.show_boxes,
                unambiguous_words=self.unambiguous_words,
                svg=self.generate_svg,
                footer=self.parse_footer
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
    generate_svg: bool = typer.Option(False, help="Generate SVG file"),
    parse_footer: bool = typer.Option(False, help="Parse the footer rather then the comic"),
):
    """Generate transcripts for Ryan North's Dinosaur Comics from https://qwantz.com"""
    set_logging_formatter()
    logger = logging.getLogger()
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
            generate_svg=generate_svg,
            parse_footer=parse_footer,
        )

        with Pool(4) as pool:
            results = pool.map(inner, image_paths)
            if unambiguous_words:
                for result in results:
                    for word in result:
                        print(word)


if __name__ == '__main__':
    app()
