# Dinosaur Comic Parser

A transcript generator for [Ryan North](https://www.ryannorth.ca/)'s [Dinosaur Comics](https://qwantz.com)

## Installation

Install `parse-qwantz` with `pip`

```bash
  pip install parse-qwantz
```

## Usage

You need to download the image file for the comic you want transcribed, for example https://qwantz.com/comics/comic2-02.png. Then run `parse-qwantz`:

```
$ parse-qwantz comic2-02.png
T-Rex: Today is a beautiful day to be stomping on things! As a dinosaur, stomping is the best part of my day indeed!

T-Rex: *gasp*

T-Rex: What's that, little house? You wish you were back in your own time? THAT IS TOO BAD FOR YOU

T-Rex: Perhaps you too will get a stomping, little girl!
Utahraptor: WAIT!

Utahraptor: Is stomping really the answer to your problem(s)?
T-Rex: Problem(s)?

T-Rex: My only problem(s) have to do with you interrupting my stomping!
T-Rex: 〚small〛 crazy utahraptor!
```

You can also call it with
```bash
python -m parse_qwantz
```

The argument can also be a directory path instead of a file path. In such case the program will run on all files in the specified directory.

## Options

### `--output-dir`

By default, the program outputs to stdout and logs to stderr. With this option, when processing file `image_name.png` it will output to `OUTPUT_DIR/image_name.png.txt` and log to `OUTPUT_DIR/image_name.log`.

### `--generate-svg`

Instead of transcribing the comic, generate a vectorized version in the SVG format and print it to the standard output.

### `--parse-footer`

Instead of transcribing the comic, transcribe just the footer.

## Conventions

Bold and italics are marked with "◖◗" and "▹◃" respectively. This is to avoid ambiguity which may result from using characters like "*" or "_".

All descriptions are in "〚〛" brackets. Each line that isn't just description starts from a "character" name followed by a colon. That "character" might be one of the actual characters, but also "Narrator", "Off panel", "Banner", "Book cover" etc.

When some text in a panel is obscured but can be reconstructed, it's in "⦃⦄" braces. So far this applies only to 2 comics: #59 and #61.

When some text in a panel is obscured and not reconstructed, it's replaced either by the special "…" character, or a description of how it's obscured in "〚〛" brackets.

## Notes

This program still does not work on all DC strips, but at this point it should work correctly on pretty much all "standard" strips and some less-standard ones (thanks to the system of overrides). Eventually all existing strips should work, including the guest comics, with updates for new comics coming out regularly.

After all comics are working, I might add some other features, like generating SVG images.

## Running Tests

To run tests, run the following command:

```bash
  pytest test/
```

## Acknowledgments

This program would not be possible without the wonderful comics by Ryan North! Thanks, Ryan, and congratulations on the 20th anniversary of your comics! Btw [the anniversary comic](https://qwantz.com/?comic=4005) will totally not work with this script, haha! (at least until I add an override)