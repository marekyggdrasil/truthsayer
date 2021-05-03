#!/bin/sh
convert FD-Fremen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 151 151 254 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim fremen_jamis.png
convert FD-Fremen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 467 151 570 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim fremen_shadout_mapes.png
convert FD-Fremen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 783 151 886 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim fremen_otheym.png
convert FD-Fremen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 310 421 413 524' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim fremen_chani.png
convert FD-Fremen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 626 421 729 524' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim fremen_stilgar.png
convert FD-Fremen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 954 419 1057 522' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim fremen_liet_kynes.png
