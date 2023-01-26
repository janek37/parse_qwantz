#!/usr/bin/env bash

number="$1"

stdout_file=test/expected_outputs/$number.txt
parse-qwantz $COMIC_DIR/"${number}"* > "$stdout_file"
cp $COMIC_DIR/"${number}"* test/comics/$number.png
