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
Panel 1:
T-Rex: Today is a beautiful day to be stomping on things! As a dinosaur, stomping is the best part of my day indeed!

Panel 2:
T-Rex: *gasp*

Panel 3:
T-Rex: What's that, little house? You wish you were back in your own time? THAT IS TOO BAD FOR YOU

Panel 4:
T-Rex: Perhaps you too will get a stomping, little girl!
Utahraptor: WAIT!

Panel 5:
Utahraptor: Is stomping really the answer to your problem(s)?
T-Rex: Problem(s)?

Panel 6:
T-Rex: My only problem(s) have to do with you interrupting my stomping!
T-Rex: (small) crazy utahraptor!
```

You can also call it with
```bash
python -m parse_qwantz
```

The argument can also be a directory path instead of a file path. In such case the program will run on all files in the specified directory.

## Options

### `--output-dir`

By default, the program outputs to stdout and logs to stderr. With this option, when processing file `image_name.png` it will output to `OUTPUT_DIR/image_name.txt` and log to `OUTPUT_DIR/image_name.log`.

## Notes

This program will not work on all DC strips. [Some](https://qwantz.com/?comic=12) [are](https://qwantz.com/?comic=45) [fairly](http://qwantz.com/?comic=70) [non-standard](https://qwantz.com/?comic=31) (including [the mirror universe](https://qwantz.com/?comic=35), [Morris the bug](https://qwantz.com/index.php?comic=674), [guest comics](https://qwantz.com/?comic=1486) etc.), while others might just not work correctly for more or less apparent reasons: there might be warning or error messages, or it might just generate an inaccurate transcript silently. It should however work correctly for most comics.

This project is in a rather early stage, and while there are no plans to support the mirror universe or [arbitrary images](https://qwantz.com/?comic=2099), there still might be some new features and some optimization.

## Running Tests

To run tests, run the following command:

```bash
  pytest test/
```

## Acknowledgments

This program would not be possible without the wonderful comics by Ryan North! Thanks, Ryan, and congratulations on the 20th anniversary of your comics! Btw [the anniversary comic](https://qwantz.com/?comic=4005) will totally not work with this script, haha!