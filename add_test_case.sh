#!/usr/bin/env bash

number="$1"
COMIC_DIR=~/media/teksty/różności/qwantz/comics

stdout_file=test/expected_outputs/$number.txt
python parse_qwantz.py $COMIC_DIR/"${number}"* > "$stdout_file"
cp $COMIC_DIR/"${number}"* test/comics/$number.png
