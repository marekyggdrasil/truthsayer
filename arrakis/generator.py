from PIL import Image

import qrcode

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


def generate(tanks, territories, texts, outfile, quality=95):
    filename = pkg_resources.open_binary(assets, 'map.png')
    canvas = Image.open(filename)
    width_canvas, height_canvas = canvas.size
    del filename
    if texts.get('qr', None) is not None:
        qr_code = makeQR(texts['qr'])
        width_qr, height_qr = qr_code.size
        pos_qr_x = 20
        pos_qr_y = int(height_canvas - height_qr - 20)
        canvas.paste(qr_code, (pos_qr_x, pos_qr_y))
    canvas = canvas.convert('RGB')
    canvas.save(outfile, quality=quality)
    del canvas
