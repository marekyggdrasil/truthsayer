#!/bin/sh
convert FD-BeneGesserit.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 151 151 254 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim bene_gesserit_alia.png
convert FD-BeneGesserit.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 467 151 570 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim bene_gesserit_margot_lady_fenring.png
convert FD-BeneGesserit.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 783 151 886 254' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim bene_gesserit_princess_irulan.png
convert FD-BeneGesserit.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 310 421 413 524' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim bene_gesserit_reverend_mother_ramallo.png
convert FD-BeneGesserit.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 626 421 729 524' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim bene_gesserit_wanna_marcus.png
convert FD-BeneGesserit.jpeg \
  -gravity Center \
  \( -size 1105x570 \
     xc:Black \
     -fill White \
     -draw 'circle 954 419 1057 522' \
     -alpha Copy \
  \) -compose CopyOpacity -composite \
  -trim bene_gesserit_mother_mohian.png
