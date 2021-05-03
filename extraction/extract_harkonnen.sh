#!/bin/sh
convert FD-Harkonnen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 151 151 254 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim harkonnen_umman_kudu.png
convert FD-Harkonnen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 467 151 570 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim harkonnen_captain_iakin_nefud.png
convert FD-Harkonnen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 783 151 886 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim harkonnen_piter_de_vries.png
convert FD-Harkonnen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 310 421 413 524' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim harkonnen_beast_rabban.png
convert FD-Harkonnen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 626 421 729 524' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim harkonnen_feyd_rautha.png
convert FD-Harkonnen.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 954 419 1057 522' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim harkonnen_baron_harkonnen.png
