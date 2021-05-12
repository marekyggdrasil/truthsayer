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


class Renderer:
    def __init__(self, game_state, game_config, outfile, troop_tokens=[], dead_leaders=[], quality=95):
        self.game_state = game_state
        self.game_config = game_config
        self.troop_edge = game_config['static']['dimensions']['troop_edge']
        self.troop_size = game_config['static']['dimensions']['troop']
        self.leader_size = game_config['static']['dimensions']['leader']
        self.factions = game_state['meta']['factions']
        self.texts = game_state['meta']['texts']
        self.dead_leaders = dead_leaders # TODO
        self.troop_tokens = troop_tokens # TODO
        self.outfile = outfile
        self.quality = quality
        # prepare canvas
        self.prepareCanvas()
        # prepare data
        self.factions_positions = self.calculateFactionLeadersPositions()

    def prepareCanvas(self):
        filename = pkg_resources.open_binary(assets, 'map.png')
        self.canvas = Image.open(filename)
        self.canvas = self.canvas.convert('RGBA')
        self.width_canvas, self.height_canvas = self.canvas.size
        del filename
        # text layer
        self.txt = Image.new('RGBA', self.canvas.size, (255,255,255,0))
        self.d = ImageDraw.Draw(self.txt)
        filename = pkg_resources.open_binary(assets, 'FreeSans.ttf')
        self.fnt = ImageFont.truetype(filename, 15)
        del filename
        filename = pkg_resources.open_binary(assets, 'RobotoCondensed-Bold.ttf')
        self.fnt_troop = ImageFont.truetype(filename, 22)
        del filename

    def renderTroop(self, x, y, faction, number):
        colors = {
            'spiritual_advisor': '#274587',
            'bene_gesserit_troops': '#274587',
            'atreides_troops': '#306C3D',
            'harkonnen_troops': '#000000',
            'emperor_troops': '#ED3337',
            'sardaukar': '#ED3337',
            'spacing_guild_troops': '#E8552C',
            'fremen_troops': '#FEC64B',
            'fedaykin': '#FEC64B'
        }
        fill = colors.get(faction, 'blue')
        box = (
            x-self.troop_size/2,
            y-self.troop_size/2,
            x+self.troop_size/2,
            y+self.troop_size/2)
        self.d.ellipse(box, fill=fill, outline ='black', width=2)
        text_fill = 'white'
        if faction in ['spiritual_advisor', 'sardaukar', 'fedaykin']:
            text_fill = 'black'
            box = (
                x-self.troop_size/2+self.troop_edge,
                y-self.troop_size/2+self.troop_edge,
                x+self.troop_size/2-self.troop_edge,
                y+self.troop_size/2-self.troop_edge)
            self.d.ellipse(box, fill='white', outline ='black', width=2)
        text = str(number)
        w, h = self.fnt_troop.getsize(text)
        self.d.text((x, y+h/2-2), text, font=self.fnt_troop, fill=text_fill, anchor='ms')

    def renderTroops(self):
        for x, y, faction, number in self.troop_tokens:
            self.renderTroop(x, y, faction, number)

    def calculateFactionLeadersPositions(self):
        positions = []
        for i in range(18):
            self.leader_r = int((self.width_canvas/2)-50)
            if i in [1, 2, 4, 5]:
                self.leader_r += 20
            reg = 2*math.pi/18
            angle = (-3*i+4)*reg+reg/2
            dx = int(self.leader_r*math.cos(angle))
            dy = int(self.leader_r*math.sin(angle))
            x = int(self.width_canvas/2)+dx-int(self.leader_size/2)
            y = int(self.height_canvas/2)+dy-int(self.leader_size/2)
            positions.append(tuple([x, y]))
        return positions

    def renderQR(self):
        if self.texts.get('qr', None) is None:
            return None
        qr_code = makeQR(self.texts['qr'])
        self.width_qr, self.height_qr = qr_code.size
        self.pos_qr_x = 20
        self.pos_qr_y = int(self.height_canvas - self.height_qr - 40)
        self.canvas.paste(qr_code, (self.pos_qr_x, self.pos_qr_y))
        self.d.text((self.pos_qr_x, self.height_canvas - 40), self.texts['promo'] + '\n' + self.texts['qr'], font=self.fnt, fill='white')
        self.d.text((self.pos_qr_x, self.height_canvas - self.height_qr - 40 - 20), self.texts['promo_top'], font=self.fnt, fill='white')

    def renderRegionMarks(self):
        # region markings
        for i in range(18):
            color = 'black'
            r = int((self.width_canvas/2)-70)
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
            x = int(self.width_canvas/2)+dx-4
            y = int(self.height_canvas/2)+dy
            self.d.text((x, y), 'R'+str(i+1), font=self.fnt, fill=color, anchor='ms')

    def renderFactionPositions(self):
        # faction info around the map of Arrakis
        for i, (faction, (x, y)) in enumerate(zip(self.factions, self.factions_positions)):
            # faction token
            filename = pkg_resources.open_binary(assets, faction)
            token = Image.open(filename)
            token = token.convert('RGBA')
            width_token, height_token = token.size
            token = token.resize((self.leader_size, self.leader_size), Image.ANTIALIAS)
            width_token, height_token = token.size
            del filename
            box_target = (x, y, x+width_token, y+height_token)
            self.canvas.paste(token, box_target, mask=token)
            # faction text info
            x_info = 0
            y_info = 0
            if i == 0:
                x_info = x + width_token + 5
                y_info = y + 40
            if i == 3:
                x_info = x + width_token + 5
                y_info = y + 5
            if i in [1, 5]:
                x_info = x
                y_info = y + width_token
            if i == 2:
                x_info = x
                y_info = y - 20 - 20
            if i == 4:
                x_info = 5
                y_info = y + width_token
            self.d.text((x_info, y_info), self.texts['usernames'][i], font=self.fnt, fill='white')

    def renderTleilaxuTanks(self):
        # dead leaders in the tleilaxu_tanks
        for x, y, disc_filename in self.dead_leaders:
            filename = pkg_resources.open_binary(assets, disc_filename)
            token = Image.open(filename)
            token = token.convert('RGBA')
            token = token.resize((self.leader_size, self.leader_size), Image.ANTIALIAS)
            width_token, height_token = token.size
            dx = int(self.leader_size/2)
            dy = int(self.leader_size/2)
            box_target = (x-dx, y-dy, x+dx, y+dy)
            self.canvas.paste(token, box_target, mask=token)

    def renderGameInfo(self):
        # game info
        reg = 2*math.pi/18
        angle = (-3*2+4)*reg+reg/2
        dx = int(self.leader_r*math.cos(angle))
        x_info = int(self.width_canvas/2)+dx-int(self.leader_size/2)
        y_info = 110
        self.d.text((x_info, y_info), self.texts['game_info'], font=self.fnt, fill='white')

    def render(self):
        self.renderQR()
        self.renderRegionMarks()
        self.renderFactionPositions()
        self.renderTleilaxuTanks()
        self.renderTroops()
        self.renderGameInfo()
        # compose the text layer
        self.canvas = Image.alpha_composite(self.canvas, self.txt)
        # remove alpha
        self.canvas = self.canvas.convert('RGB')
        self.canvas.save(self.outfile, quality=self.quality)
        del self.canvas


def placeSpice(canvas, d, amount, x, y, outfile, spice_size=46, quality=95):
    filename = pkg_resources.open_binary(assets, 'light_lens_flare.png')
    token = Image.open(filename)
    token = token.convert('RGBA')
    width_token, height_token = token.size
    token = token.resize((spice_size, spice_size), Image.ANTIALIAS)
    width_token, height_token = token.size
    del filename
    filename = pkg_resources.open_binary(assets, 'RobotoCondensed-Bold.ttf')
    fnt_troop = ImageFont.truetype(filename, 22)
    del filename
    box_target = (
        int(x-width_token/2),
        int(y-width_token/2),
        int(x+width_token/2),
        int(y+height_token/2))
    canvas.paste(token, box_target, mask=token)
    text = str(amount)
    w, h = fnt_troop.getsize(text)
    d.text((x+w/4, y+h/2), text, font=fnt_troop, fill='black', anchor='ms')


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
