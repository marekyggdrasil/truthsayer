import math
import json

from shapely.geometry import Polygon
from shapely.geometry.point import Point

from simpleai.search.local import genetic

from brackette.memento import OriginatorJSON

from truthsayer.opti import TokenPlacementProblem
from truthsayer.opti import MultiTokenPlacementProblem
from truthsayer.renderer import Renderer


try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

from truthsayer import assets


class ConfigManager:
    def __init__(self):
        json_file = pkg_resources.read_text(assets, 'game_config.json')
        self.game_config = json.loads(json_file)
        all_areas = list(self.game_config['generated']['areas']['circles'].keys())
        all_areas += list(self.game_config['generated']['areas']['polygons'].keys())
        self.all_areas = list(set(all_areas))

    def isLeader(self, name):
        return name in self.game_config['types']['tokens']['leaders']

    def isTroop(self, name):
        return name in self.game_config['types']['tokens']['troop_tokens']

    def getRadius(self, element):
        diameter = None
        if self.isLeader(element):
            diameter = game_config['dimensions']['leader']
        elif self.isTroop(element):
            diameter = game_config['dimensions']['troop']
        radius = diameter/2
        return radius

    def getAreas(self):
        return self.all_areas

    def isAreaPoint(self, area_name):
        return area_name in self.game_config['types']['areas']['point']

    def isAreaPlayerPosition(self, area_name):
        return area_name in self.game_config['types']['areas']['players']

    def isAreaSpice(self, area_name):
        return area_name in self.game_config['types']['areas']['spice']

    def getPolygonArea(self, area_name):
        return self.game_config['generated']['areas']['polygons'][area_name]

    def getCenter(self):
         cx = self.game_config['generated']['map_center']['x']
         cy = self.game_config['generated']['map_center']['y']
         cr = self.game_config['generated']['map_center']['r']+7
         return cx, cy, cr

    def getFile(self, token_name):
        return self.game_config['files'][token_name]

    def getFactionSymbol(self, faction_name):
        return self.game_config['faction_symbols'][faction_name]

    def getFactionName(self, faction_key):
        return self.game_config['faction_names'][faction_key]

class RenderingProcessor:
    def __init__(self):
        self.manager = ConfigManager()
        self.game_config = self.manager.game_config

    def prepareInstance(game_state, area_name, region_name):
        polygons_maximize_overlap = Polygon(self.manager.getPolygonArea(area_name))
        # print(polygons_maximize_overlap.svg())
        # print(polygons_maximize_overlap.area)
        if region_name != 'whole':
            # print('making region')
            polygons_region = Polygon(self.manager.getPolygonArea(region_name))
            # print(polygons_region.svg())
            # print(polygons_region.area)
            polygons_maximize_overlap = polygons_maximize_overlap.intersection(polygons_region)
            # print(polygons_maximize_overlap.svg())
            # print(polygons_maximize_overlap.area)
        avoid_overlap_areas = []
        if area_name not in game_state['visual'].keys():
            game_state['visual'][area_name] = {}
        if region_name not in game_state['visual'][area_name].keys():
            game_state['visual'][area_name][region_name] = {}
        for token_name in game_state['visual'][area_name][region_name].keys():
            element_object = game_state['visual'][area_name][region_name][token_name]
            x = element_object['x']
            y = element_object['y']
            radius = self.manager.getRadius(token_name)
            polygon_token = Point(x, y).buffer(radius)
            avoid_overlap_areas.append(polygon_token)
        return polygons_maximize_overlap, avoid_overlap_areas


    def placeSingleToken(self, game_state, area_name, region_name, element_name, tolerance=0.01, amount=0):
        target_radius = self.manager.getRadius(element_name)
        polygons_maximize_overlap, avoid_overlap_areas = self.prepareInstance(game_state, area_name, region_name)
        problem = TokenPlacementProblem(polygons_maximize_overlap, avoid_overlap_areas, target_radius, tolerance=0.01)
        result = genetic(problem, population_size=75, mutation_chance=0.15, iterations_limit=120)
        x, y = result.state
        token_type = None
        if self.manager.isLeader(element_name):
            token_type = 'leader'
        if self.manager.isTroop(element_name):
            token_type = 'troop_token'
        game_state['visual'][area_name][region_name][element_name] = {
            'token': element_name,
            'type': token_type,
            'x': x,
            'y': y,
            'c': amount
        }
        return result.state


    def placeMultipleTokens(self, game_state, area_name, region_name, names, amounts):
        target_radii = [self.manager.getRadius(name) for name in names]
        polygons_maximize_overlap, avoid_overlap_areas = self.prepareInstance(game_state, area_name, region_name)
        problem = MultiTokenPlacementProblem(polygons_maximize_overlap, avoid_overlap_areas, target_radii, tolerance=0.01)
        result = genetic(problem, population_size=75, mutation_chance=0.2, iterations_limit=100)
        for i, (name, amount) in enumerate(zip(names, amounts)):
            x = result.state[i*2]
            y = result.state[i*2+1]
            token_type = None
            print('multiplace')
            print(name)
            if self.manager.isLeader(name):
                token_type = 'leader_token'
            elif self.manager.isTroop(name):
                token_type = 'troop_token'
            game_state['visual'][area_name][region_name][name] = {
                'token': name,
                'type': token_type,
                'x': x,
                'y': y,
                'c': amount
            }
        return result.state

    def calculateStormPosition(self, position):
        cx, cy, cr = self.manager.getCenter()
        angle = (position-6.5)*360/18
        angle_rot = angle - 90
        angle_rad = 2*math.pi*(-angle)/360
        x = cx+math.cos(angle_rad)*cr
        y = cy+math.sin(angle_rad)*cr
        storm_object = {
            'token': self.manager.getFile('storm'),
            'x': x,
            'y': y,
            's': 0.5,
            'a': angle_rot,
        }
        return storm_object

    def calculateWheel(self, value):
        return 360*(value+1.25)/21

    def process(self, game_state):
        # find objects which should be rendered but have no coordinates
        to_place = {}
        for area in self.manager.getAreas():
            if area in game_state['areas'].keys():
                if area not in game_state['visual'].keys():
                    game_state['visual'][area] = {}
                if self.manager.isAreaPoint(area):
                    if self.manager.isAreaSpice(area):
                        value = game_state['areas'][area]
                        game_state['visual'][area] = value
                    continue
                for region in game_state['areas'][area].keys():
                    # print(region)
                    if type(game_state['areas'][area][region]) is not dict:
                        continue
                    # print(region)
                    for token in game_state['areas'][area][region].keys():
                        if token not in game_state['visual'][area].keys():
                            if area not in to_place:
                                to_place[area] = {}
                            if region not in to_place[area].keys():
                                to_place[area][region] = {}
                            to_place[area][region][token] = game_state['areas'][area][region][token]
        if 'storm' in game_state['areas'].keys():
            position = game_state['areas']['storm']
            storm_object = self.calculateStormPosition(position)
            game_state['visual']['storm'] = storm_object
        for area, faction in game_state['meta']['factions'].items():
            faction_symbol = self.manager.getFactionSymbol(faction)
            file = self.manager.getFile(faction_symbol)
            print(faction, faction_symbol, file)
            game_state['visual'][area] = file
        wheel_values = ['wheel_attacker_value', 'wheel_defender_value']
        for wheel in wheel_values:
            if wheel in game_state['areas'].keys():
                value = game_state['areas'][wheel]
                game_state['visual'][wheel] = self.calculateWheel(value)
        wheel_leaders = ['wheel_attacker_leader', 'wheel_defender_leader']
        for wheel in wheel_leaders:
            if wheel in game_state['areas'].keys():
                leader = game_state['areas'][wheel]
                file = self.manager.getFile(leader)
                game_state['visual'][wheel] = file
        wheel_players = ['wheel_attacker_player', 'wheel_defender_player']
        wheel_players_refs = {}
        for wheel in wheel_players:
            if wheel in game_state['areas'].keys():
                player_key = game_state['areas'][wheel]
                faction_key = game_state['meta']['factions'][player_key]
                faction_name = self.manager.getFactionName(faction_key)
                player_name = game_state['meta']['usernames'][player_key]
                game_state['visual'][wheel + '_faction'] = faction_name
                game_state['visual'][wheel + '_name'] = player_name
                wheel_players_refs[wheel + '_faction'] = wheel
                wheel_players_refs[wheel + '_name'] = wheel
        # optimize positions of tokens that need placement
        for area_name in to_place.keys():
            for region_name in to_place[area_name].keys():
                elements = to_place[area_name][region_name]
                print(elements)
                print(len(elements.keys()))
                if len(elements.keys()) > 1:
                    amounts = []
                    names = []
                    for element_name in elements.keys():
                        element_amount = elements[element_name]
                        amounts.append(element_amount)
                        names.append(element_name)
                    placeMultipleTokens(game_state, area_name, region_name, names, amounts)
                    continue
                for element_name in elements.keys():
                    element_amount = elements[element_name]
                    placeSingleToken(game_state, area_name, region_name, element_name, amount=element_amount)
                continue
        # find objects which have coordinates but should be removed
        to_remove = []
        to_remove_points = []
        for area in game_state['visual'].keys():
            if area in ['wheel_attacker_cards', 'wheel_defender_cards']:
                continue
            if self.manager.isAreaPoint(area):
                if self.manager.isAreaPlayerPosition(area):
                    continue
                if area not in game_state['areas'].keys():
                    to_remove_points.append(area)
                continue
            if area == 'storm':
                if 'storm' not in game_state['areas'].keys():
                    to_remove_points.append(area)
                continue
            if area in wheel_values + wheel_leaders:
                if area not in game_state['areas'].keys():
                    to_remove_points.append(area)
                continue
            if area in wheel_players_refs.keys():
                wheel = wheel_players_refs[area]
                if wheel not in game_state['areas'].keys():
                    to_remove_points.append(area)
                continue
            for token_object in game_state['visual'][area]:
                if type(token_object) is str:
                    continue
                region = token_object['region']
                token = token_object['token']
                removal = None
                if area not in game_state['areas'].keys():
                    removal = area, region, token
                elif region not in game_state['areas'][area].keys():
                    removal = area, region, token
                elif token not in game_state['areas'][area][region].keys():
                    removal = area, region, token
                if removal is not None:
                    to_remove.append(removal)
        # remove gathered
        for area in to_remove_points:
            del game_state['visual'][area]
        for area, region, token in to_remove:
            del game_state['visual'][area][region][token]
        # as a last thing, generate texts
        for player_key, faction_key in game_state['meta']['factions'].items():
            player_name = game_state['meta']['usernames'][player_key]
            faction_name = self.manager.getFactionName(faction_key)
            text = '{0}\n{1}'.format(player_name, faction_name)
            if 'texts' not in game_state['meta'].keys():
                game_state['meta']['texts'] = {}
            if 'usernames' not in game_state['meta']['texts'].keys():
                game_state['meta']['texts']['usernames'] = {}
            game_state['meta']['texts']['usernames'][player_key] = text
        return game_state


class OriginatorTruthsayer(OriginatorJSON):
    def __init__(self, game_state={}, meta={}):
        if game_state == {}:
            game_state = self.initiate(meta)
        super().__init__(game_state)
        self.processor = RenderingProcessor()
        self.card_objects = {} # TODO

    def move(self, source_area, source_region, target_area, target_region, faction, N, unit=None):
        pass

    def ship(self, faction, target_area, target_region, N):
        pass

    def change(self, target_area, target_region, N):
        pass

    # payee is the one receiving
    def pay(self, spice, payor, payee):
        pass

    def kill(self, leader, area=None, region=None, N=1):
        pass

    def revive(self, leader_or_unit, N=1):
        pass

    def lead(self, leader):
        pass

    def treachery(self, faction, card):
        pass

    def battle(self, faction, N):
        pass

    def storm(self, region):
        pass

    def initiate(self, meta):
        _object_state = {
            'hidden': {},
            'areas': {},
            'visual': {},
            'meta': meta
        }
        return _object_state

    def render(self, outfile, battle=False):
       self._object_state = self.processor.process(self._object_state)
       self.backup()
       renderer = Renderer(
           self._object_state,
           self.processor.game_config,
           self.card_objects,
           outfile,
           battle=battle)
       renderer.render()
