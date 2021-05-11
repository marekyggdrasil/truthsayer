from PIL import Image, ImageDraw

from arrakis.generator import placeSpice

sourcefile = 'images/arrakis.jpg'
outfile = 'images/spicy.jpg'

quality = 95
spice_size = 600

canvas = Image.open(sourcefile)
canvas = canvas.convert('RGBA')

txt = Image.new('RGBA', canvas.size, (255, 255, 255, 0))
d = ImageDraw.Draw(txt)

placeSpice(canvas, d, 12, 480, 110, outfile, spice_size=spice_size, quality=quality)
placeSpice(canvas, d, 8, 970, 220, outfile, spice_size=spice_size, quality=quality)
placeSpice(canvas, d, 6, 650, 780, outfile, spice_size=spice_size, quality=quality)

canvas = Image.alpha_composite(canvas, txt)
canvas = canvas.convert('RGB')
canvas.save(outfile, quality=quality)
