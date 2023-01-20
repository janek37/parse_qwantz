#!/usr/bin/env bash

number="$1"

stdout_file=test/expected_outputs/$number.txt
python parse_qwantz.py ~/media/teksty/różności/qwantz/comics/"${number}"* > "$stdout_file"
cp ~/media/teksty/różności/qwantz/comics/"${number}"* test/comics/$number.png
