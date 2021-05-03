#!/bin/sh
convert FD-Emperor.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 151 151 254 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim emperor_bashar.png
convert FD-Emperor.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 467 151 570 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim emperor_burseg.png
convert FD-Emperor.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 783 151 886 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim emperor_caid.png
convert FD-Emperor.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 310 421 413 524' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim emperor_captain_aramsham.png
convert FD-Emperor.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 626 421 729 524' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim emperor_count_hasimir_fenring.png
convert FD-Emperor.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 954 419 1057 522' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim emperor_emperor_shaddam_iv.png
