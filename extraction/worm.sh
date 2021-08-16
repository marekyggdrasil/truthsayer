convert worm.jpeg \
        -gravity Center \
        -stroke black -strokewidth 60 \
        -draw 'fill-opacity 0 circle 360 300 660 300' worm_token.png
convert worm_token.png \
        -gravity Center \
        \( -size 1044x1166 \
        xc:Black \
        -fill White -stroke black -strokewidth 0 \
        -draw 'circle 360 300 660 300' \
        -alpha Copy \
        \) \
        -compose CopyOpacity -composite \
        -trim worm_token.png
convert worm_token.png -scale 293x293 worm_token.png
