#!/bin/sh
convert FD-Atreides.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 151 151 254 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim atreides_dr_yueh.png
convert FD-Atreides.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 467 151 570 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim atreides_duncan_idaho.png
convert FD-Atreides.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 783 151 886 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim atreides_gurney_halleck.png
convert FD-Atreides.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 310 421 413 524' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim atreides_lady_jessica.png
convert FD-Atreides.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 626 421 729 524' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim atreides_thufir_hawat.png
convert FD-Atreides.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 954 419 1057 522' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim atreides_paul_muaddib.png
