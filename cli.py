from pathlib import Path

import typer

from parse_qwantz import main


def cli(image_path: Path, debug: bool = typer.Option(False, help="Enable debug features.")):
    """Generate transcripts for Ryan North's Dinosaur Comics from https://qwantz.com"""
    main(image_path, debug=debug)


if __name__ == '__main__':
    typer.run(cli)
