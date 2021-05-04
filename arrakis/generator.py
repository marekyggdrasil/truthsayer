from PIL import Image

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


def generate(factions, tanks, territories, texts, outfile, quality=95):
    leader_size = 90
    filename = pkg_resources.open_binary(assets, 'map.png')
    canvas = Image.open(filename)
    canvas = canvas.convert('RGBA')
    width_canvas, height_canvas = canvas.size
    del filename
    if texts.get('qr', None) is not None:
        qr_code = makeQR(texts['qr'])
        width_qr, height_qr = qr_code.size
        pos_qr_x = 20
        pos_qr_y = int(height_canvas - height_qr - 20)
        canvas.paste(qr_code, (pos_qr_x, pos_qr_y))
    for i, faction in enumerate(factions):
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
        angle = (3*i+4)*reg+reg/2
        dx = int(r*math.cos(angle))
        dy = int(r*math.sin(angle))
        x = int(width_canvas/2)+dx-int(width_token/2)
        y = int(height_canvas/2)+dy-int(height_token/2)
        box_target = (x, y, x+width_token, y+height_token)
        canvas.paste(token, box_target, mask=token)
    canvas = canvas.convert('RGB')
    canvas.save(outfile, quality=quality)
    del canvas
