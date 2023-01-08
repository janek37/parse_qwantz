#!/usr/bin/env bash

filename="$1"

tempdir=$(mktemp -d)

masked="$tempdir/masked.png"
convert "$filename" img/mask.png -compose plus -composite "$masked"

convert "$masked" -crop 244x243+0+0 "$tempdir/panel1.png"
convert "$masked" -crop 130x243+244+0 "$tempdir/panel2.png"
convert "$masked" -crop 361x243+374+0 "$tempdir/panel3.png"
convert "$masked" -crop 195x245+0+243 "$tempdir/panel4.png"
convert "$masked" -crop 295x245+195+243 "$tempdir/panel5.png"
convert "$masked" -crop 242x245+493+243 "$tempdir/panel6.png"

echo "$tempdir"
