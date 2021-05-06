from PIL import Image, ImageDraw, ImageFont

import qrcode
import math

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

from arrakis import assets


def makeQR(data, box_size=4, border=4):
    QR = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=box_size,
        border=border,
    )
    QR.add_data(data)
    QR.make(fit=True)
    qr_code = QR.make_image(fill_color="black", back_color="white")
    return qr_code


def generate(factions, tanks, territories, dead_leaders, texts, outfile, quality=95):
    leader_size = 90
    filename = pkg_resources.open_binary(assets, 'map.png')
    canvas = Image.open(filename)
    canvas = canvas.convert('RGBA')
    width_canvas, height_canvas = canvas.size
    del filename
    # text layer
    txt = Image.new('RGBA', canvas.size, (255,255,255,0))
    d = ImageDraw.Draw(txt)
    filename = pkg_resources.open_binary(assets, 'FreeSans.ttf')
    fnt = ImageFont.truetype(filename, 15)
    del filename
    # images
    if texts.get('qr', None) is not None:
        qr_code = makeQR(texts['qr'])
        width_qr, height_qr = qr_code.size
        pos_qr_x = 20
        pos_qr_y = int(height_canvas - height_qr - 40)
        canvas.paste(qr_code, (pos_qr_x, pos_qr_y))
        d.text((pos_qr_x, height_canvas - 40), texts['promo'] + '\n' + texts['qr'], font=fnt, fill='white')
        d.text((pos_qr_x, height_canvas - height_qr - 40 - 20), texts['promo_top'], font=fnt, fill='white')
    # region markings
    for i in range(18):
        color = 'black'
        r = int((width_canvas/2)-70)
        if i not in [12, 13]:
            r += 40
            color = 'white'
        if 6 < i < 16:
            r -= 10
        reg = 2*math.pi/18
        angle = (-i+5)*reg
        if i in [2, 4, 10, 13]:
            angle += reg/7
        else:
            angle += 6*reg/7
        dx = int(r*math.cos(angle))
        dy = int(r*math.sin(angle))
        x = int(width_canvas/2)+dx-4
        y = int(height_canvas/2)+dy
        d.text((x, y), 'R'+str(i+1), font=fnt, fill=color, anchor='ms')
    # faction info around the map of Arrakis
    for i, faction in enumerate(factions):
        # faction token
        filename = pkg_resources.open_binary(assets, faction)
        token = Image.open(filename)
        token = token.convert('RGBA')
        width_token, height_token = token.size
        token = token.resize((leader_size, leader_size), Image.ANTIALIAS)
        width_token, height_token = token.size
        del filename
        r = int((width_canvas/2)-50)
        if i in [1, 2, 4, 5]:
            r += 20
        reg = 2*math.pi/18
        angle = (-3*i+4)*reg+reg/2
        dx = int(r*math.cos(angle))
        dy = int(r*math.sin(angle))
        x = int(width_canvas/2)+dx-int(width_token/2)
        y = int(height_canvas/2)+dy-int(height_token/2)
        box_target = (x, y, x+width_token, y+height_token)
        canvas.paste(token, box_target, mask=token)
        # faction text info
        x_info = 0
        y_info = 0
        if i == 0:
            x_info = int(width_canvas/2)+dx+int(width_token/2) + 5
            y_info = y + 40
        if i == 3:
            x_info = int(width_canvas/2)+dx+int(width_token/2) + 5
            y_info = y + 5
        if i in [1, 5]:
            x_info = x
            y_info = int(height_canvas/2)+dy+int(width_token/2)
        if i == 2:
            x_info = x
            y_info = int(height_canvas/2)+dy-int(width_token/2)-20-20
        if i == 4:
            x_info = 5
            y_info = int(height_canvas/2)+dy+int(width_token/2)
        d.text((x_info, y_info), texts['usernames'][i], font=fnt, fill='white')
    # dead leaders in the tleilaxu_tanks
    for x, y, disc_filename in dead_leaders:
        filename = pkg_resources.open_binary(assets, disc_filename)
        token = Image.open(filename)
        token = token.convert('RGBA')
        token = token.resize((leader_size, leader_size), Image.ANTIALIAS)
        width_token, height_token = token.size
        dx = int(width_token/2)
        dy = int(height_token/2)
        box_target = (x-dx, y-dy, x+dx, y+dy)
        canvas.paste(token, box_target, mask=token)
    # game info
    reg = 2*math.pi/18
    angle = (-3*2+4)*reg+reg/2
    dx = int(r*math.cos(angle))
    x_info = int(width_canvas/2)+dx-int(width_token/2)
    y_info = 110
    d.text((x_info, y_info), texts['game_info'], font=fnt, fill='white')
    # compose the text layer
    canvas = Image.alpha_composite(canvas, txt)
    # remove alpha
    canvas = canvas.convert('RGB')
    canvas.save(outfile, quality=quality)
    del canvas


def generateNeighborhood(centers, locations, neighbors, regions, outfile, quality=95, skip=[]):
    dl = 10
    filename = pkg_resources.open_binary(assets, 'map.png')
    canvas = Image.open(filename)
    canvas = canvas.convert('RGBA')
    width_canvas, height_canvas = canvas.size
    del filename
    filename = pkg_resources.open_binary(assets, 'FreeSans.ttf')
    fnt = ImageFont.truetype(filename, 25)
    del filename
    # drawing layer
    layer = Image.new('RGBA', canvas.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(layer)
    # region markings
    for i in range(18):
        r = int((width_canvas/2)-25)
        reg = 2*math.pi/18
        angle = (-i+5)*reg+reg/2
        dx = int(r*math.cos(angle))
        dy = int(r*math.sin(angle))
        x = int(width_canvas/2)+dx
        y = int(height_canvas/2)+dy
        draw.text((x, y), 'R'+str(i+1), font=fnt, fill='white', anchor='ms')
    # mark centers
    for location in locations:
        if location in skip:
            continue
        x, y = centers[location]
        x = int(x)
        y = int(y)
        draw.ellipse((x-dl, y-dl, x+dl, y+dl), fill='blue', outline='blue')
        if location in regions.keys():
            regs = regions[location]
            txt = ', '.join(regs)
            if location == 'polar_sink':
                txt = 'neutral'
            draw.text((x, y+3*dl), txt, font=fnt, fill='green', anchor='ms')
    # mark neighbors
    for (loc1, loc2) in neighbors:
        if loc1 in skip or loc2 in skip:
            continue
        x1, y1 = centers[loc1]
        x1 = int(x1)
        y1 = int(y1)
        x2, y2 = centers[loc2]
        x2 = int(x2)
        y2 = int(y2)
        draw.line((x1, y1, x2, y2), fill='blue', width=2)
    # compose the text layer
    canvas = Image.alpha_composite(canvas, layer)
    # remove alpha
    canvas = canvas.convert('RGB')
    canvas.save(outfile, quality=quality)
    del canvas
