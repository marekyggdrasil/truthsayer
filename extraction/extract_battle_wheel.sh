#!/bin/sh
convert battle_wheel_numbers.png \
  -gravity Center \
  \( -size 940x940 \
     xc:Black \
     -fill White \
     -draw 'circle 470 470 940 470' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim battle_wheel_numbers_transparent.png
