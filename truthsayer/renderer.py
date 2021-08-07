from PIL import Image, ImageDraw, ImageFont

import textwrap
import qrcode
import math
import json

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

from truthsayer import assets
from truthsayer.assets import json_files


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
    def __init__(self, game_state, game_config, card_objects, outfile, troop_tokens=[], dead_leaders=[], quality=95, battle=False):
        self.deck_generator = json.loads(pkg_resources.read_text(json_files, 'generated_decks.json'))
        self.txt_spacing_wheel = 5
        self.card_unit = 8
        self.card_radius = 10
        self.card_spacing = 10
        self.game_state = game_state
        self.game_config = game_config
        self.card_objects = card_objects
        self.battle = battle
        self.troop_edge = game_config['dimensions']['troop_edge']
        self.troop_size = game_config['dimensions']['troop']
        self.leader_size = game_config['dimensions']['leader']
        self.spice_size = game_config['dimensions']['spice']
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
        filename = pkg_resources.open_binary(assets, 'FreeSans.ttf')
        self.fnt_wheel = ImageFont.truetype(filename, 27)
        del filename
        filename = pkg_resources.open_binary(assets, 'FreeSans.ttf')
        self.fnt_card_large = ImageFont.truetype(filename, 24)
        del filename
        filename = pkg_resources.open_binary(assets, 'FreeSans.ttf')
        self.fnt_card_small = ImageFont.truetype(filename, 19)
        del filename
        filename = pkg_resources.open_binary(assets, 'FreeSans.ttf')
        self.fnt_card_tiny = ImageFont.truetype(filename, 13)
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
        areas = self.game_config['generated']['areas']['polygons']
        type_point = self.game_config['types']['areas']['point']
        for area_name, region_object in self.game_state['visual'].items():
            if area_name in type_point:
                continue
            if area_name == 'storm':
                continue
            if type(region_object) is str:
                continue
            if area_name.startswith('wheel_'):
                continue
            # print('region object')
            # print(region_object)
            for region_name, token_object in region_object.items():
                # print('token object')
                # print(token_object)
                if region_name[0] != 'R' and region_name != 'whole':
                    continue
                for token_name, token_instance in token_object.items():
                    # print('token instnace')
                    # print(token_instance)
                    x = token_instance['x']
                    y = token_instance['y']
                    token_type = token_instance['type']
                    if token_type == 'troop_token':
                        faction = token_instance['token']
                        number = token_instance['c']
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
        self.pos_qr_x = int(self.width_canvas-self.width_qr-20)
        self.pos_qr_y = int(self.height_canvas - self.height_qr - 40)
        self.canvas.paste(qr_code, (self.pos_qr_x, self.pos_qr_y))

        w, h = self.fnt.getsize(self.texts['promo'])
        w2, h2 = self.fnt.getsize(self.texts['qr'])
        if w2 > w:
            w = w2
        x = int(self.width_canvas-w-20)
        y = self.height_canvas - 40
        text = self.texts['promo'] + '\n' + self.texts['qr']
        self.canvas, w, h = self.renderText(text, self.fnt, 'white', x, y, anchor=None)

        text = self.texts['promo_top']
        w, h = self.fnt.getsize(text)
        x = int(self.width_canvas-w-20)
        y = self.height_canvas - self.height_qr - 40 - 20
        self.canvas, w, h = self.renderText(text, self.fnt, 'white', x, y, anchor=None)

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
        for i in range(1, 7):
            area_name = 'player_{0}'.format(str(i))
            token_name = self.game_state['visual'].get(area_name, None)
            if token_name is None:
                continue
            filename = pkg_resources.open_binary(assets, token_name)
            token = Image.open(filename)
            token = token.convert('RGBA')
            width_token, height_token = token.size
            token = token.resize((self.leader_size, self.leader_size), Image.ANTIALIAS)
            width_token, height_token = token.size
            del filename
            x, y = self.game_config['generated']['areas']['circles'][area_name]
            half_width = int(width_token/2)
            half_height = int(height_token/2)
            if y - half_height < 0:
                y += half_height - y
            elif y + half_height > self.height_canvas:
                y -= (y + half_height) - self.height_canvas
            box_target = (x-half_width, y-half_height, x+half_width, y+half_height)
            self.canvas.paste(token, box_target, mask=token)
            # faction text info
            x_info = 0
            y_info = 0
            if i == 1:
                x_info = x + half_width + 5
                y_info = y
            if i == 4:
                x_info = x + half_width + 5
                y_info = 5
            if i == 2:
                x_info = x - half_width
                y_info = y + half_width
            if i == 6:
                x_info = x - width_token
                y_info = y + half_width
            if i == 3:
                x_info = x - half_width
                y_info = y - half_height - 20 - 20
            if i == 5:
                x_info = 5
                y_info = y + half_width
            text = self.texts['player_names'][area_name] + '\n' + self.texts['user_ids'][area_name]
            self.d.text((x_info, y_info), text, font=self.fnt, fill='white')

    def renderTleilaxuTanks(self):
        if 'tleilaxu_tanks' not in self.game_state['visual'].keys():
            return None
        if 'whole' not in self.game_state['visual']['tleilaxu_tanks'].keys():
            return None
        values = self.deck_generator['traitor_deck']['values']
        for leader, token_instance in self.game_state['visual']['tleilaxu_tanks']['whole'].items():
            for entry in values:
                token_name = entry[0]
                if leader != token_name:
                    continue
                leader_faction = entry[2]
                disc_filename = leader_faction + '_' + leader + '.png'
                x = int(token_instance['x'])
                y = int(token_instance['y'])
                filename = pkg_resources.open_binary(assets, disc_filename)
                token = Image.open(filename)
                token = token.convert('RGBA')
                token = token.resize((self.leader_size, self.leader_size), Image.ANTIALIAS)
                width_token, height_token = token.size
                dx = int(self.leader_size/2)
                dy = int(self.leader_size/2)
                box_target = (x-dx, y-dy, x+dx, y+dy)
                self.canvas.paste(token, box_target, mask=token)
                break

    def renderGameInfo(self):
        # game info
        reg = 2*math.pi/18
        angle = (-3*2+4)*reg+reg/2
        dx = int(self.leader_r*math.cos(angle))
        x_info = int(self.width_canvas/2)+dx-int(self.leader_size/2)
        y_info = 110
        game_info = 'Game {0}\nTurn {1}\n{2} phase'.format(self.texts['game_id'], str(self.texts['game_turn']), self.texts['game_phase'])
        text = game_info
        self.canvas, w, h = self.renderText(text, self.fnt, 'white', x_info, y_info, anchor=None)

    def renderLastCommands(self):
        text = '\n'.join(self.texts['commands'])
        lh = 0
        for cmd in self.texts['commands']:
            _, h = self.fnt.getsize(text)
            lh += h
        x_info = 20
        y_info = int(self.height_canvas-lh-20)
        self.canvas, _, _ = self.renderText(text, self.fnt, 'white', x_info, y_info, anchor=None)

    def render(self):
        self.placeStorm()
        self.renderRegionMarks()
        self.renderFactionPositions()
        self.renderTleilaxuTanks()
        self.renderTroops()
        self.placeSpice()
        # compose the text layer
        self.canvas = Image.alpha_composite(self.canvas, self.txt)
        self.renderBattle()
        self.renderQR()
        self.renderGameInfo()
        self.renderLastCommands()
        # remove alpha
        self.canvas = self.canvas.convert('RGB')
        self.canvas.save(self.outfile, quality=self.quality)
        del self.canvas

    def placeSpice(self):
        params = self.game_state['configs'].get('spice_token', ['czempak_spice_1', self.spice_size])
        if params[1] is None:
            params[1] = self.spice_size
        filename = params[0] + '.png'
        spice_size = params[1]
        filename = pkg_resources.open_binary(assets, filename)
        token = Image.open(filename)
        token = token.convert('RGBA')
        width_token, height_token = token.size
        token = token.resize((spice_size, spice_size), Image.ANTIALIAS)
        width_token, height_token = token.size
        del filename
        filename = pkg_resources.open_binary(assets, 'RobotoCondensed-Bold.ttf')
        fnt_troop = ImageFont.truetype(filename, 22)
        del filename
        half_width = int(width_token/2)
        half_height = int(height_token/2)
        for area_name, amount in self.game_state['visual'].items():
            if area_name.endswith('_spice'):
                x, y = self.game_config['generated']['areas']['circles'][area_name]
                box_target = (
                    int(x-width_token/2),
                    int(y-width_token/2),
                    int(x+width_token/2),
                    int(y+height_token/2))
                self.canvas.paste(token, box_target, mask=token)
                text = str(amount)
                w, h = fnt_troop.getsize(text)
                self.d.text((x+w/4, y+h/2), text, font=self.fnt_troop, fill='black', anchor='ms')

    def placeStorm(self):
        storm_object = self.game_state['visual'].get('storm', None)
        if storm_object is None:
            return
        filename = pkg_resources.open_binary(assets, storm_object['token'])
        token = Image.open(filename)
        token = token.convert('RGBA')
        width_token, height_token = token.size
        scale = storm_object['s']
        angle = storm_object['a']
        x = storm_object['x']
        y = storm_object['y']
        token = token.resize((int(scale*width_token), int(scale*height_token)), Image.ANTIALIAS)
        token = token.rotate(angle, Image.NEAREST, expand=1)
        width_token, height_token = token.size
        del filename
        x_diff = int(math.ceil(x - int(math.floor(width_token/2))))
        if x_diff < 0:
            box = (
                -x_diff,
                0,
                width_token,
                height_token
            )
            token = token.crop(box)
            width_token, height_token = token.size
            x = 0
        else:
            x -= int(math.floor(width_token/2))
        y_diff = int(math.ceil(y - int(math.floor(height_token/2))))
        if y_diff < 0:
            box = (
                0,
                -y_diff,
                width_token,
                height_token
            )
            token = token.crop(box)
            width_token, height_token = token.size
            y = 0
        else:
            y -= int(math.floor(height_token/2))
        y_diff = int(math.ceil(y - int(math.floor(height_token/2))))
        box_target = (
            int(x),
            int(y),
            int(x+width_token),
            int(y+height_token))
        self.canvas.paste(token, box_target, mask=token)

    # ref: https://code-maven.com/slides/python/rectangle-with-rounded-corners
    def round_corner(self, radius, fill):
        corner = Image.new('RGBA', (radius, radius), (0, 0, 0, 0))
        draw = ImageDraw.Draw(corner)
        draw.pieslice((0, 0, radius * 2, radius * 2), 180, 270, fill=fill)
        return corner

    # ref: https://code-maven.com/slides/python/rectangle-with-rounded-corners
    def round_rectangle(self, size, radius, fill):
        width, height = size
        rectangle = Image.new('RGBA', size, fill)
        corner = self.round_corner(radius, fill)
        rectangle.paste(corner, (0, 0))
        rectangle.paste(corner.rotate(90), (0, height - radius))  # Rotate the corner and paste it
        rectangle.paste(corner.rotate(180), (width - radius, height - radius))
        rectangle.paste(corner.rotate(270), (width - radius, 0))
        return rectangle

    def render_card(self, card_object):
        radius = self.card_radius
        fill = 'white'
        # card = self.round_rectangle(size, radius, fill)
        params = self.game_state['configs'].get('card_background', ['czempak_card_background', self.card_unit])
        filename = params[0] + '.png'
        unit = params[1]
        filename = pkg_resources.open_binary(assets, filename)
        width = 25*unit
        height = 35*unit
        size = width, height
        token = Image.open(filename)
        token = token.convert('RGBA')
        width_token, height_token = token.size
        token = token.resize((width, height), Image.ANTIALIAS)
        width_token, height_token = token.size
        del filename
        card = token
        # render card content
        text = card_object['header']
        x, y = 10, 10
        for line in textwrap.wrap(text, width=12):
            card, w, h = self.renderText(line, self.fnt_card_large, 'white', x, y, anchor=None, canvas=card)
            y += h + 9
        y += 10
        text = card_object['description']
        for line in textwrap.wrap(text, width=30):
            card, w, h = self.renderText(line, self.fnt_card_tiny, 'white', x, y, anchor=None, canvas=card)
            y += 14
        text = card_object['type']
        text_subtype = card_object.get('subtype', None)
        if text_subtype is not None:
            text += ' / ' + text_subtype
        x, y = 10, height_token - 12 - h
        card, w, h = self.renderText(text, self.fnt_card_small, 'white', x, y, anchor=None, canvas=card)
        return card, width, height

    def placeWheel(self, x, y, width, angle, username_area=None, faction_area=None, leader=None):
        filename = pkg_resources.open_binary(assets,
        'battle_wheel_numbers.png')
        token = Image.open(filename)
        token = token.convert('RGBA')
        width_token, height_token = token.size
        token = token.resize((width, width), Image.ANTIALIAS)
        token = token.rotate(angle, Image.NEAREST, expand=1)
        width_token, height_token = token.size
        del filename
        box_target = (
            int(x-width_token/2),
            int(y-height_token/2),
            int(x+width_token/2),
            int(y+height_token/2))
        self.canvas.paste(token, box_target, mask=token)
        # top of the wheel
        filename = pkg_resources.open_binary(assets,
                                             'battle_wheel_top.png')
        token = Image.open(filename)
        token = token.convert('RGBA')
        width_token, height_token = token.size
        token = token.resize((width, width), Image.ANTIALIAS)
        width_token, height_token = token.size
        del filename
        box_target = (
            int(x-width_token/2),
            int(y-height_token/2),
            int(x+width_token/2),
            int(y+height_token/2))
        self.canvas.paste(token, box_target, mask=token)
        if leader is not None:
            filename = pkg_resources.open_binary(assets, leader)
            token = Image.open(filename)
            token = token.convert('RGBA')
            token = token.resize((self.leader_size, self.leader_size), Image.ANTIALIAS)
            width_token, height_token = token.size
            dx = int(self.leader_size/2)
            dy = int(self.leader_size/2)
            half_width = int(width/4)
            box_target = (x+half_width-dx, y+half_width-dy, x+half_width+dx, y+half_width+dy)
            self.canvas.paste(token, box_target, mask=token)
        y_txt = y + self.txt_spacing_wheel
        if username_area is not None:
            text = self.game_state['visual'][username_area]
            self.canvas, w, h = self.renderText(text, self.fnt_wheel, 'black', x, y_txt, ycenter=True)
            y_txt += h
            y_txt += self.txt_spacing_wheel
        if faction_area is not None:
            text = self.game_state['visual'][faction_area]
            self.canvas, w, h = self.renderText(text, self.fnt_wheel, 'black', x, y_txt, ycenter=True)

    def renderText(self, text, font, fill, x, y, anchor='ms', ycenter=False, canvas=None):
        if canvas is None:
            canvas = self.canvas
        w, h = self.fnt_troop.getsize(text)
        txt = Image.new('RGBA', canvas.size, (255,255,255,0))
        draw = ImageDraw.Draw(txt)
        yt = y
        if ycenter:
            yt = y+h/2-2
        draw.text((x, yt), text, font=font, fill=fill, anchor=anchor)
        canvas = Image.alpha_composite(canvas, txt)
        return canvas, w, h

    def renderBattle(self):
        if not self.battle:
            return None
        TINT_COLOR = (0, 0, 0)  # Black
        TRANSPARENCY = 0.65  # Degree of transparency, 0-100%
        OPACITY = int(255 * TRANSPARENCY)
        overlay = Image.new('RGBA', self.canvas.size, TINT_COLOR+(0,))
        draw = ImageDraw.Draw(overlay)  # Create a context for drawing things on it.
        draw.rectangle(
            (
                (0, 0),
                (self.width_canvas, self.height_canvas)
            ),
            fill=TINT_COLOR+(OPACITY,))
        self.canvas = Image.alpha_composite(self.canvas, overlay)
        # place left wheel
        xthird = int(self.width_canvas/3)
        ythird = int(self.height_canvas/3)
        x = int(xthird-xthird/5)
        y = int(ythird-ythird/3)
        # attacker cards
        cards = self.game_state['areas'].get('wheel_attacker_cards', None)
        width = xthird
        if cards is not None:
            for j, key in enumerate(cards):
                card_object = self.card_objects[key]
                card, w, h = self.render_card(card_object)
                half_width = int(w/2)
                half_height = int(h/2)
                xoff = j*(w+self.card_spacing)-int(len(cards)*(w+self.card_spacing)/2)
                box_target = (x+xoff, y-half_height, x+xoff+w, y+half_height)
                self.canvas.paste(card, box_target, mask=card)
            y += width + self.card_spacing
        angle = self.game_state['visual']['wheel_attacker_value']
        leader = self.game_state['visual'].get('wheel_attacker_leader', None)
        username_area = 'wheel_attacker_player_name'
        faction_area = 'wheel_attacker_player_faction'
        self.placeWheel(x, y, width, angle, username_area=username_area, faction_area=faction_area, leader=leader)
        # place right wheel
        x = self.width_canvas-int(xthird-xthird/5)
        y = self.height_canvas-int(ythird-ythird/3)
        cards = self.game_state['areas'].get('wheel_defender_cards', None)
        if cards is not None:
            for j, key in enumerate(cards):
                card_object = self.card_objects[key]
                card, w, h = self.render_card(card_object)
                half_width = int(w/2)
                half_height = int(h/2)
                xoff = j*(w+self.card_spacing)-int(len(cards)*(w+self.card_spacing)/2)
                box_target = (x+xoff, y-half_height, x+xoff+w, y+half_height)
                self.canvas.paste(card, box_target, mask=card)
            y -= width + self.card_spacing
        angle = self.game_state['visual']['wheel_defender_value']
        leader = self.game_state['visual'].get('wheel_defender_leader', None)
        username_area = 'wheel_defender_player_name'
        faction_area = 'wheel_defender_player_faction'
        self.placeWheel(x, y, width, angle, username_area=username_area, faction_area=faction_area, leader=leader)


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
