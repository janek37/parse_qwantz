#!/usr/bin/env bash

filename="$1"

tempdir=$(mktemp -d)

masked="$tempdir/masked.png"
convert "$filename" img/mask.png -compose plus -composite "$masked"

convert "$masked" -crop 239x239+3+2 "$tempdir/panel1.png"
convert "$masked" -crop 126x239+246+2 "$tempdir/panel2.png"
convert "$masked" -crop 358x239+375+2 "$tempdir/panel3.png"
convert "$masked" -crop 190x239+3+244 "$tempdir/panel4.png"
convert "$masked" -crop 295x239+196+244 "$tempdir/panel5.png"
convert "$masked" -crop 239x239+494+244 "$tempdir/panel6.png"

echo "$tempdir"
