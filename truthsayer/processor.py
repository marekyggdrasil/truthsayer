import math
import random
import json

from shapely.geometry import Polygon
from shapely.geometry.point import Point

from simpleai.search.local import genetic

from brackette.memento import OriginatorJSON, Caretaker

from truthsayer.opti import TokenPlacementProblem
from truthsayer.opti import MultiTokenPlacementProblem
from truthsayer.renderer import Renderer


try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

from truthsayer import assets
from truthsayer.assets import json_files


class CardsManager:
    def __init__(self):
        self.deck_treachery = json.loads(pkg_resources.read_text(json_files, 'treachery_deck.json'))['treachery_deck']
        self.headers_deck_treachery = []
        for card in self.deck_treachery:
            self.headers_deck_treachery.append(card['card'])
        self.deck_alliance = json.loads(pkg_resources.read_text(json_files, 'alliance_deck.json'))['alliance_deck']
        self.headers_deck_alliance = []
        for card in self.deck_alliance:
            self.headers_deck_alliance.append(card['card'])
        self.deck_spice = json.loads(pkg_resources.read_text(json_files, 'spice_deck.json'))['spice_deck']
        self.headers_deck_spice = []
        for card in self.deck_spice:
            self.headers_deck_spice.append(card['card'])
        self.deck_generator = json.loads(pkg_resources.read_text(json_files, 'generated_decks.json'))
        self.generateStormDeck()
        self.generateTraitorDeck()
        self.generateCardIndex()

    def generateStormDeck(self):
        cards = []
        headers = []
        template = self.deck_generator['storm_deck']['template']
        values = self.deck_generator['storm_deck']['values']
        for entry in values:
            card = {
                'card': template['card'].format(*entry),
                'sectors': template['sectors'].format(*entry),
                'header': template['header'].format(*entry),
                'description': template['description'].format(*entry)
            }
            cards.append(card)
            headers.append(str(entry[0]) + '_sectors')
        self.deck_storm = cards
        self.headers_deck_storm = headers

    def generateTraitorDeck(self):
        cards = []
        headers = []
        template = self.deck_generator['traitor_deck']['template']
        values = self.deck_generator['traitor_deck']['values']
        for entry in values:
            card = {
                'card': template['card'].format(*entry),
                'header': template['header'].format(*entry),
                'faction': template['faction'].format(*entry),
                'strength': template['strength'].format(*entry),
                'description': template['description'].format(*entry)
            }
            cards.append(card)
            headers.append('traitor_' + entry[0])
        self.deck_traitor = cards
        self.headers_deck_traitor = headers

    def generateCardIndex(self):
        self.card_objects = {}
        all_cards = self.deck_treachery
        all_cards += self.deck_alliance
        all_cards += self.deck_spice
        all_cards += self.deck_storm
        all_cards += self.deck_traitor
        for card in all_cards:
            self.card_objects[card['card']] = card

class ConfigManager:
    def __init__(self):
        self.deck_generator = json.loads(pkg_resources.read_text(json_files, 'generated_decks.json'))
        json_file = pkg_resources.read_text(assets, 'game_config.json')
        self.game_config = json.loads(json_file)
        all_territories = list(self.game_config['generated']['territories']['circles'].keys())
        all_territories += list(self.game_config['generated']['territories']['polygons'].keys())
        self.all_territories = list(set(all_territories))

    def isLeader(self, name):
        return name in self.game_config['types']['tokens']['leaders']

    def isTroop(self, name):
        return name in self.game_config['types']['tokens']['troop_tokens']

    def isTroopSpecial(self, name):
        if not self.isTroop(name):
            raise ValueError('{0} is not a troop token at all'.format(name))
        if name in ['spiritual_advisor', 'fedaykin', 'sardaukar']:
            return True
        return False

    def getGamePhases(self):
        return ['setup', 'storm', 'spice_blow', 'nexus', 'choam_charity', 'bidding', 'revival', 'shipment_and_movement', 'battle', 'spice_harvest', 'mentat_pause']

    def getGamePhasesChoices(self):
        phases = self.getGamePhases()
        choices = []
        for phase in phases:
            choices.append({
                'name': (phase+'_phase').replace('_', ' ').title(),
                'value': phase
            })
        return choices

    def isGamePhaseValid(self, phase):
        return phase in self.getGamePhases()

    def getRadius(self, element):
        diameter = None
        if self.isLeader(element):
            diameter = self.game_config['dimensions']['leader']
        elif self.isTroop(element):
            diameter = self.game_config['dimensions']['troop']
        elif element == 'worm':
            diameter = self.game_config['dimensions']['leader']
        radius = diameter/2
        return radius

    def getAreas(self):
        return self.all_territories

    def getTroopTypes(self, faction):
        troop_types = [faction + '_troops']
        if faction == 'bene_gesserit':
            troop_types.append('spiritual_advisor')
        if faction == 'fremen':
            troop_types.append('fedaykin')
        if faction == 'emperor':
            troop_types.append('sardaukar')
        return troop_types

    def getTroopTypesAll(self):
        troop_types = [faction + '_troops' for faction in self.getFactions()]
        troop_types.append('spiritual_advisor')
        troop_types.append('fedaykin')
        troop_types.append('sardaukar')
        return troop_types

    def getTroopTypesChoices(self, sort=False, reverse=False, swap=False):
        troop_types = self.getTroopTypesAll()
        choices = []
        for troop_type in troop_types:
            troop_type_value = troop_type.replace('_', ' ').title()
            name, value = troop_type, troop_type_value
            if swap:
                value, name = troop_type, troop_type_value
            choices.append({
                'name': name,
                'value': value
            })
        if sort:
            options = sorted(choices, key=lambda choice: len(choice['name']), reverse=True)
        return choices

    def getFactionFromTroopType(self, troop_type):
        for faction in self.getFactions():
            if troop_type == faction + '_troops':
                return faction
        if troop_type == 'spiritual_advisor':
            return 'bene_gesserit'
        if troop_type == 'fedaykin':
            return 'fremen'
        if troop_type == 'sardaukar':
            return 'emperor'
        return None

    def getRegions(self):
        return self.game_config['generated']['sectors']

    def getRegionsChoices(self, sort=False, reverse=False, swap=False):
        sectors = self.getRegions()
        choices = []
        for sector in sectors:
            sector_value = sector.replace('S', 'Sector ')
            name, value = sector, sector_value
            if swap:
                value, name = sector, sector_value
            choices.append({
                'name': name,
                'value': value
            })
        if sort:
            options = sorted(choices, key=lambda choice: len(choice['name']), reverse=True)
        return choices

    def getLocationsOfSectors(self):
        data = {}
        for location, sectors in self.game_config['generated']['location_sectors'].items():
            if location == 'arrakis':
                continue
            for sector in sectors:
                if sector not in data.keys():
                    data[sector] = []
                data[sector].append(location)
                data[sector] = list(set(data[sector]))
        return data

    def getLocations(self):
        return self.game_config['generated']['locations']

    def getLocationsChoices(self, sort=False, reverse=False, swap=False):
        locations = self.getLocations()
        choices = []
        for location in locations:
            if location == 'arrakis':
                continue
            location_name = location.replace('_', ' ').title()
            name, value = location, location_name
            if swap:
                value, name = location, location_name
            choices.append({
                'name': name,
                'value': value
            })
        if sort:
            choices = sorted(choices, key=lambda choice: len(choice['name']), reverse=reverse)
        return choices

    def getFactions(self):
        return self.game_config['faction_names'].keys()

    def getFactionsChoices(self, sort=False, reverse=False, swap=False):
        choices = []
        for faction, faction_name in self.game_config['faction_names'].items():
            name, value = faction, faction_name
            if swap:
                value, name = faction, faction_name
            choices.append({
                'name': name,
                'value': value
            })
        if sort:
            choices = sorted(choices, key=lambda choice: len(choice['name']), reverse=reverse)
        return choices

    def getLeaders(self, faction):
        selected = []
        values = self.deck_generator['traitor_deck']['values']
        for entry in values:
            leader = entry[0]
            leader_name = entry[1]
            leader_faction = entry[2]
            if leader_faction == faction:
                selected.append(leader)
        return selected

    def getLeadersFaction(self, leader):
        selected = []
        values = self.deck_generator['traitor_deck']['values']
        for entry in values:
            leader_id = entry[0]
            leader_faction = entry[2]
            if leader_id == leader:
                return leader_faction
        return None

    def getLeadersNamesStrength(self, lst):
        selected = []
        values = self.deck_generator['traitor_deck']['values']
        for entry in values:
            leader = entry[0]
            if leader in lst:
                selected.append(entry)
        return selected

    def getLeadersChoices(self, faction, sort=False, reverse=False, swap=False):
        choices = []
        values = self.deck_generator['traitor_deck']['values']
        for entry in values:
            leader = entry[0]
            leader_name = entry[1]
            leader_faction = entry[2]
            if leader_faction != faction:
                continue
            name, value = leader, leader_name
            if swap:
                value, name = leader, leader_name
            choices.append({
                'name': name,
                'value': value
            })
        if sort:
            choices = sorted(choices, key=lambda choice: choice['name'], reverse=reverse)
        return choices


    def getSpiceAreasChoices(self, sort=False, reverse=False, swap=False):
        choices = []
        for territory in self.game_config['types']['territories']['spice']:
            territory_value = territory.replace('_spice', '')
            territory_name = territory_value.replace('_', ' ').title()
            name, value = territory_name, territory_value
            if swap:
                value, name = territory_name, territory_value
            choices.append({
                'name': name,
                'value': value
            })
        if sort:
            choices = sorted(choices, key=lambda choice: choice['name'], reverse=reverse)
        return choices


    def getDeckChoices(self):
        return [
            {
                'name': 'Treachery deck',
                'value': 'treachery'
            },
            {
                'name': 'Spice deck',
                'value': 'spice'
            },
            {
                'name': 'Storm deck',
                'value': 'storm'
            },
            {
                'name': 'Traitor deck',
                'value': 'traitor'
            }
        ]


    def isAreaPoint(self, territory_name):
        return territory_name in self.game_config['types']['territories']['point']

    def isAreaPlayerPosition(self, territory_name):
        return territory_name in self.game_config['types']['territories']['players']

    def isAreaSpice(self, territory_name):
        return territory_name in self.game_config['types']['territories']['spice']

    def getPolygonArea(self, territory_name):
        return self.game_config['generated']['territories']['polygons'][territory_name]

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

    def prepareInstance(self, game_state, territory_name, sector_name):
        polygons_maximize_overlap = Polygon(self.manager.getPolygonArea(territory_name))
        # print(polygons_maximize_overlap.svg())
        # print(polygons_maximize_overlap.territory)
        if sector_name != 'whole':
            # print('making sector')
            polygons_region = Polygon(self.manager.getPolygonArea(sector_name))
            # print(polygons_region.svg())
            # print(polygons_region.territory)
            polygons_maximize_overlap = polygons_maximize_overlap.intersection(polygons_region)
            # print(polygons_maximize_overlap.svg())
            # print(polygons_maximize_overlap.territory)
        avoid_overlap_territories = []
        if territory_name not in game_state['visual'].keys():
            game_state['visual'][territory_name] = {}
        if sector_name not in game_state['visual'][territory_name].keys():
            game_state['visual'][territory_name][sector_name] = {}
        for token_name in game_state['visual'][territory_name][sector_name].keys():
            element_object = game_state['visual'][territory_name][sector_name][token_name]
            x = element_object['x']
            y = element_object['y']
            radius = self.manager.getRadius(token_name)
            polygon_token = Point(x, y).buffer(radius)
            avoid_overlap_territories.append(polygon_token)
        return polygons_maximize_overlap, avoid_overlap_territories


    def placeSingleToken(self, game_state, territory_name, sector_name, element_name, tolerance=0.01, amount=0):
        target_radius = self.manager.getRadius(element_name)
        polygons_maximize_overlap, avoid_overlap_territories = self.prepareInstance(game_state, territory_name, sector_name)
        problem = TokenPlacementProblem(polygons_maximize_overlap, avoid_overlap_territories, target_radius, tolerance=0.01)
        result = genetic(problem, population_size=75, mutation_chance=0.15, iterations_limit=120)
        x, y = result.state
        token_type = 'leader_like'
        if self.manager.isLeader(element_name):
            token_type = 'leader'
        if self.manager.isTroop(element_name):
            token_type = 'troop_token'
        game_state['visual'][territory_name][sector_name][element_name] = {
            'token': element_name,
            'type': token_type,
            'x': x,
            'y': y,
            'c': amount
        }
        return result.state


    def placeMultipleTokens(self, game_state, territory_name, sector_name, names, amounts):
        target_radii = [self.manager.getRadius(name) for name in names]
        polygons_maximize_overlap, avoid_overlap_territories = self.prepareInstance(game_state, territory_name, sector_name)
        problem = MultiTokenPlacementProblem(polygons_maximize_overlap, avoid_overlap_territories, target_radii, tolerance=0.01)
        result = genetic(problem, population_size=75, mutation_chance=0.2, iterations_limit=100)
        for i, (name, amount) in enumerate(zip(names, amounts)):
            x = result.state[i*2]
            y = result.state[i*2+1]
            token_type = 'leader_like'
            # print('multiplace')
            # print(name)
            if self.manager.isLeader(name):
                token_type = 'leader_token'
            elif self.manager.isTroop(name):
                token_type = 'troop_token'
            game_state['visual'][territory_name][sector_name][name] = {
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
        for territory in self.manager.getAreas():
            if territory in game_state['territories'].keys():
                if territory not in game_state['visual'].keys():
                    game_state['visual'][territory] = {}
                if self.manager.isAreaPoint(territory):
                    if self.manager.isAreaSpice(territory):
                        value = game_state['territories'][territory]
                        game_state['visual'][territory] = value
                    continue
                for sector in game_state['territories'][territory].keys():
                    if type(game_state['territories'][territory][sector]) is not dict:
                        continue
                    for token in game_state['territories'][territory][sector].keys():
                        if territory in game_state['visual'].keys():
                            if sector in game_state['visual'][territory].keys():
                                if token in game_state['visual'][territory][sector].keys():
                                    old_count = game_state['visual'][territory][sector][token]['c']
                                    new_count = game_state['territories'][territory][sector][token]
                                    if new_count == 0:
                                        del game_state['visual'][territory][sector][token]
                                    elif old_count != new_count:
                                        game_state['visual'][territory][sector][token]['c'] = new_count
                                    continue
                        if territory not in to_place:
                            to_place[territory] = {}
                        if sector not in to_place[territory].keys():
                            to_place[territory][sector] = {}
                        to_place[territory][sector][token] = game_state['territories'][territory][sector][token]
        if 'storm' in game_state['territories'].keys():
            position = game_state['territories']['storm']
            storm_object = self.calculateStormPosition(position)
            game_state['visual']['storm'] = storm_object
        for territory, faction in game_state['meta']['factions'].items():
            faction_symbol = self.manager.getFactionSymbol(faction)
            file = self.manager.getFile(faction_symbol)
            # print(faction, faction_symbol, file)
            game_state['visual'][territory] = file
        wheel_values = ['wheel_attacker_value', 'wheel_defender_value']
        for wheel in wheel_values:
            if wheel in game_state['territories'].keys():
                value = game_state['territories'][wheel]
                game_state['visual'][wheel] = self.calculateWheel(value)
        wheel_leaders = ['wheel_attacker_leader', 'wheel_defender_leader']
        for wheel in wheel_leaders:
            if wheel in game_state['territories'].keys():
                leader = game_state['territories'][wheel]
                if leader is not None:
                    file = self.manager.getFile(leader)
                    game_state['visual'][wheel] = file
        wheel_players = ['wheel_attacker_player', 'wheel_defender_player']
        wheel_players_refs = {}
        for wheel in wheel_players:
            if wheel in game_state['territories'].keys():
                faction_key = game_state['territories'][wheel]
                player_key = None
                for f, key in game_state['meta']['factions'].items():
                    if key == faction_key:
                        player_key = f
                if player_key is None:
                    continue
                faction_name = self.manager.getFactionName(faction_key)
                player_name = game_state['meta']['usernames'][player_key]
                game_state['visual'][wheel + '_faction'] = faction_name
                game_state['visual'][wheel + '_name'] = player_name
                wheel_players_refs[wheel + '_faction'] = wheel
                wheel_players_refs[wheel + '_name'] = wheel
        # optimize positions of tokens that need placement
        for territory_name in to_place.keys():
            for sector_name in to_place[territory_name].keys():
                elements = to_place[territory_name][sector_name]
                # print(elements)
                # print(len(elements.keys()))
                if len(elements.keys()) > 1:
                    amounts = []
                    names = []
                    for element_name in elements.keys():
                        element_amount = elements[element_name]
                        amounts.append(element_amount)
                        names.append(element_name)
                    self.placeMultipleTokens(game_state, territory_name, sector_name, names, amounts)
                    continue
                for element_name in elements.keys():
                    element_amount = elements[element_name]
                    self.placeSingleToken(game_state, territory_name, sector_name, element_name, amount=element_amount)
                continue
        # find objects which have coordinates but should be removed
        to_remove = []
        to_remove_points = []
        for territory in game_state['visual'].keys():
            if territory in ['wheel_attacker_cards', 'wheel_defender_cards']:
                continue
            if self.manager.isAreaPoint(territory):
                if self.manager.isAreaPlayerPosition(territory):
                    continue
                if territory not in game_state['territories'].keys():
                    to_remove_points.append(territory)
                continue
            if territory == 'storm':
                if 'storm' not in game_state['territories'].keys():
                    to_remove_points.append(territory)
                continue
            if territory in wheel_values + wheel_leaders:
                if territory not in game_state['territories'].keys():
                    to_remove_points.append(territory)
                continue
            if territory in wheel_players_refs.keys():
                wheel = wheel_players_refs[territory]
                if wheel not in game_state['territories'].keys():
                    to_remove_points.append(territory)
                continue
            for token_sector in game_state['visual'][territory].keys():
                for token in game_state['visual'][territory][token_sector].keys():
                    sector = token_sector
                    removal = None
                    if territory not in game_state['territories'].keys():
                        removal = territory, sector, token
                    elif sector not in game_state['territories'][territory].keys():
                        removal = territory, sector, token
                    elif token not in game_state['territories'][territory][sector].keys():
                        removal = territory, sector, token
                    # print(removal)
                    if removal is not None:
                        to_remove.append(removal)
        # remove gathered
        for territory in to_remove_points:
            del game_state['visual'][territory]
        for territory, sector, token in to_remove:
            del game_state['visual'][territory][sector][token]
        # as a last thing, generate texts
        for player_key, faction_key in game_state['meta']['factions'].items():
            player_name = game_state['meta']['usernames'][player_key]
            user_id = game_state['meta']['user_ids'][player_key]
            faction_name = self.manager.getFactionName(faction_key)
            text = '{0}\n{1}'.format(player_name, faction_name)
            if 'texts' not in game_state['meta'].keys():
                game_state['meta']['texts'] = {}
            if 'player_names' not in game_state['meta']['texts'].keys():
                game_state['meta']['texts']['player_names'] = {}
            if 'user_ids' not in game_state['meta']['texts'].keys():
                game_state['meta']['texts']['user_ids'] = {}
            game_state['meta']['texts']['player_names'][player_key] = player_name
            game_state['meta']['texts']['user_ids'][player_key] = user_id
        return game_state


class OriginatorTruthsayer(OriginatorJSON):
    def __init__(self, game_state={}, meta={}):
        self.processor = RenderingProcessor()
        self.cards_manager = CardsManager()
        if game_state == {}:
            game_state = self.initiate(meta)
        super().__init__(game_state)

    def validateMapLocation(self, target_territory, target_sector):
        if target_territory not in self.processor.manager.getAreas():
            raise ValueError('Invalid territory')
        if target_sector[0] != 'S' and target_sector != 'whole':
            raise ValueError('Invalid sector')

    def getAreasOfPresence(self, faction):
        troop_types = self.processor.manager.getTroopTypes(faction)
        territories = {}
        for territory, content in self._object_state['territories'].items():
            if type(content) is not dict:
                continue
            for sector in content.keys():
                for troop_type in troop_types:
                    if troop_type in content[sector].keys():
                        if content[sector][troop_type] > 0:
                            if territory not in territories.keys():
                                territories[territory] = {}
                            if sector not in territories[territory].keys():
                                territories[territory][sector] = {}
                            territories[territory][sector][troop_type] = content[sector][troop_type]
        return territories

    def getAvailableReserves(self, faction):
        if faction not in self._object_state['hidden']['reserves'].keys():
            raise ValueError('Incorrect faction')
        return self._object_state['hidden']['reserves'][faction]

    def getAvailableCards(self, faction):
        if faction not in self._object_state['hidden']['cards'].keys():
            raise ValueError('Incorrect faction')
        return self._object_state['hidden']['cards'][faction]

    def getSelectedCards(self, faction):
        participants = [
            self._object_state['territories']['wheel_attacker_player'],
            self._object_state['territories']['wheel_defender_player']
        ]
        if faction not in participants:
            raise ValueError('Player is not a battle participant')
        key = 'wheel_attacker_cards'
        if faction == participants[1]:
            key = 'wheel_defender_cards'
        return self._object_state['territories'][key]

    def move(self, faction, source_territory, source_sector, target_territory, target_sector, N, troop_type=None):
        self.validateMapLocation(source_territory, source_sector)
        self.validateMapLocation(target_territory, target_sector)
        if troop_type is None:
            troop_type = '{0}_troops'.format(faction)
        if source_territory not in self._object_state['territories'].keys():
            raise ValueError('No troops in this territory')
        if source_sector not in self._object_state['territories'][source_territory].keys():
            raise ValueError('No troops in this sector')
        if troop_type not in self._object_state['territories'][source_territory][source_sector].keys():
            raise ValueError('No troops in this sector')
        if self._object_state['territories'][source_territory][source_sector][troop_type] < N:
            raise ValueError('Insufficient amount of troops to perform this action')
        if target_territory not in self._object_state['territories'].keys():
            self._object_state['territories'][target_territory] = {}
        if target_sector not in self._object_state['territories'][target_territory].keys():
            self._object_state['territories'][target_territory][target_sector] = {}
        if troop_type not in self._object_state['territories'][target_territory][target_sector].keys():
            self._object_state['territories'][target_territory][target_sector][troop_type] = 0
        self._object_state['territories'][source_territory][source_sector][troop_type] -= N
        self._object_state['territories'][target_territory][target_sector][troop_type] += N
        cmd = '/{0} {1} {2} {3} {4} {5} {6}'.format('move', faction, source_territory, source_sector, target_territory, target_sector, str(N))
        self.appendCMD(cmd)

    def ship(self, faction, target_territory, target_sector, N, troop_type=None):
        self.validateMapLocation(target_territory, target_sector)
        if faction not in self._object_state['hidden']['reserves'].keys():
            raise ValueError('Incorrect faction')
        if troop_type is None:
            troop_type = '{0}_troops'.format(faction)
        if troop_type not in self._object_state['hidden']['reserves'][faction].keys():
            raise ValueError('Invalid troop type')
        if self._object_state['hidden']['reserves'][faction][troop_type] < N:
            raise ValueError('Not enough forces in reserves')
        if target_territory not in self._object_state['territories'].keys():
            self._object_state['territories'][target_territory] = {}
        if target_sector not in self._object_state['territories'][target_territory].keys():
            self._object_state['territories'][target_territory][target_sector] = {}
        if troop_type not in self._object_state['territories'][target_territory][target_sector].keys():
            self._object_state['territories'][target_territory][target_sector][troop_type] = 0
        self._object_state['territories'][target_territory][target_sector][troop_type] += N
        self._object_state['hidden']['reserves'][faction][troop_type] -= N
        cmd = '/{0} {1} {2} {3} {4}'.format('ship', faction, target_territory, target_sector, str(N))
        self.appendCMD(cmd)

    def placeLeader(self, faction, target_territory, target_sector, leader):
        self.validateMapLocation(target_territory, target_sector)
        if target_territory not in self._object_state['territories'].keys():
            self._object_state['territories'][target_territory] = {}
        if target_sector not in self._object_state['territories'][target_territory].keys():
            self._object_state['territories'][target_territory][target_sector] = {}
        if leader not in self._object_state['territories'][target_territory][target_sector].keys():
            self._object_state['territories'][target_territory][target_sector][leader] = 1
        else:
            # take leader back to reserves
            self._object_state['territories'][target_territory][target_sector][leader] = 0
            self._object_state['hidden']['leaders'][faction].append(leader)
            cmd = '/{0} {1} {2} {3} {4}'.format('placeLeader', faction, target_territory, target_sector, leader)
            self.appendCMD(cmd)
            return None
        found = False
        if leader in self._object_state['hidden']['leaders'][faction]:
            found = True
            self._object_state['hidden']['leaders'][faction].remove(leader)
        elif leader == self._object_state['territories']['wheel_attacker_leader']:
            found = True
            self._object_state['territories']['wheel_attacker_leader'] = None
        elif leader == self._object_state['territories']['wheel_defender_leader']:
            found = True
            self._object_state['territories']['wheel_defender_leader'] = None
        if not found:
            raise ValueError('Leader not found in available resources')
        cmd = '/{0} {1} {2} {3} {4}'.format('placeLeader', faction, target_territory, target_sector, leader)
        self.appendCMD(cmd)

    def worm(self, target_territory, target_sector):
        self.validateMapLocation(target_territory, target_sector)
        if target_territory not in self._object_state['territories'].keys():
            self._object_state['territories'][target_territory] = {}
        if target_sector not in self._object_state['territories'][target_territory].keys():
            self._object_state['territories'][target_territory][target_sector] = {}
        token = 'worm'
        if token not in self._object_state['territories'][target_territory][target_sector].keys():
            self._object_state['territories'][target_territory][target_sector][token] = 1
        else:
            del self._object_state['territories'][target_territory][target_sector][token]
        cmd = '/{0} {1} {2}'.format('worm', target_territory, target_sector)
        self.appendCMD(cmd)

    def turn(self, N):
        if N < 1:
            raise ValueError('Turn has to be greater or equal than 1')
        self._object_state['meta']['texts']['game_turn'] = N
        cmd = '/{0} {1}'.format('turn', str(N))
        self.appendCMD(cmd)

    def phase(self, name):
        if not self.processor.manager.isGamePhaseValid(name):
            raise ValueError('Invalid game phase')
        self._object_state['meta']['texts']['game_phase'] = name
        cmd = '/{0} {1}'.format('phase', name)
        self.appendCMD(cmd)

    def change(self, faction, target_territory, target_sector):
        if faction != 'bene_gesserit':
            raise ValueError('Only Bene Gesserit can change unit types')
        if target_territory not in self._object_state['territories'].keys():
            raise ValueError('Not enough troops')
        if target_sector not in self._object_state['territories'][target_territory].keys():
            raise ValueError('Not enough troops')
        available = self._object_state['territories'][target_territory][target_sector].keys()
        if 'bene_gesserit_troops' in available:
            source_troop_type = 'bene_gesserit_troops'
            target_troop_type = 'spiritual_advisor'
        elif 'bene_gesserit_troops' in available:
            target_troop_type = 'bene_gesserit_troops'
            source_troop_type = 'spiritual_advisor'
        else:
            raise ValueError('Not enough troops')
        n = self._object_state['territories'][target_territory][target_sector][source_troop_type]
        del self._object_state['territories'][target_territory][target_sector][source_troop_type]
        self._object_state['territories'][target_territory][target_sector][target_troop_type] = n
        cmd = '/{0} {1} {2}'.format('change', target_territory, target_sector)
        self.appendCMD(cmd)

    # payee is the one receiving
    def pay(self, spice, payor, payee):
        if self._object_state['hidden']['spice'][payor] < spice:
            raise ValueError('Insufficient funds')
        self._object_state['hidden']['spice'][payor] -= spice
        if payee != 'spice_bank':
            self._object_state['hidden']['spice'][payee] += spice
        cmd = '/{0} {1} {2} {3}'.format('pay', spice, payor, payee)
        self.appendCMD(cmd)

    def spiceblow(self, target_territory, N):
        target_territory_spice = target_territory + '_spice'
        if not self.processor.manager.isAreaSpice(target_territory_spice):
            raise ValueError('Invalid target territory')
        if target_territory not in self._object_state['territories'].keys():
            self._object_state['territories'][target_territory_spice] = 0
        self._object_state['territories'][target_territory_spice] += N
        cmd = '/{0} {1} {2}'.format('spiceblow', target_territory, str(N))
        self.appendCMD(cmd)

    def harvest(self, faction, target_territory, N):
        target_territory_spice = target_territory + '_spice'
        if not self.processor.manager.isAreaSpice(target_territory_spice):
            raise ValueError('Invalid target territory')
        if target_territory not in self._object_state['territories'].keys():
            self._object_state['territories'][target_territory_spice] = 0
        if self._object_state['territories'][target_territory_spice] < N:
            raise ValueError('Insufficient spice supply')
        self._object_state['territories'][target_territory_spice] -= N
        self._object_state['hidden']['spice'][faction] += N
        cmd = '/{0} {1} {2} {3}'.format('harvest', faction, target_territory_spice, str(N))
        self.appendCMD(cmd)

    def killLeader(self, leader):
        if not self.processor.manager.isLeader(leader):
            raise ValueError('Invalid leader')
        faction = self.processor.manager.getLeadersFaction(leader)
        if leader not in self._object_state['hidden']['leaders'][faction]:
            raise ValueError('Leader not in players hand')
        self._object_state['hidden']['leaders'][faction].remove(leader)
        if 'tleilaxu_tanks' not in self._object_state['territories'].keys():
            self._object_state['territories']['tleilaxu_tanks'] = {
                'whole': {}
            }
        self._object_state['territories']['tleilaxu_tanks']['whole'][leader] = 1
        cmd = '/{0} {1}'.format('kill', leader)
        self.appendCMD(cmd)

    def kill(self, faction, source_territory, source_sector, n, troop_type):
        if source_territory not in self._object_state['territories'].keys():
            raise ValueError('Not enough troops')
        if source_sector not in self._object_state['territories'][source_territory].keys():
            raise ValueError('Not enough troops')
        available = self._object_state['territories'][source_territory][source_sector].keys()
        if troop_type not in available:
            raise ValueError('Not enough troops')
        if self._object_state['territories'][source_territory][source_sector][troop_type] < n:
            raise ValueError('Not enough troops')
        self._object_state['territories'][source_territory][source_sector][troop_type] -= n
        if 'tleilaxu_tanks' not in self._object_state['territories'].keys():
            self._object_state['territories']['tleilaxu_tanks'] = {
                'whole': {}
            }
        if 'whole' not in self._object_state['territories']['tleilaxu_tanks'].keys():
            self._object_state['territories']['tleilaxu_tanks'] = {
                'whole': {}
            }
        if troop_type not in self._object_state['territories']['tleilaxu_tanks']['whole'].keys():
            self._object_state['territories']['tleilaxu_tanks']['whole'][troop_type] = 0
        self._object_state['territories']['tleilaxu_tanks']['whole'][troop_type] += n

    def reviveLeader(self, leader):
        if not self.processor.manager.isLeader(leader):
            raise ValueError('Invalid leader')
        if 'tleilaxu_tanks' not in self._object_state['territories'].keys():
            raise ValueError('Leader not in Tleilaxu Tanks')
        if 'whole' not in self._object_state['territories']['tleilaxu_tanks'].keys():
            raise ValueError('Leader not in Tleilaxu Tanks')
        if leader not in self._object_state['territories']['tleilaxu_tanks']['whole'].keys():
            raise ValueError('Leader not in Tleilaxu Tanks')
        faction = self.processor.manager.getLeadersFaction(leader)
        del self._object_state['territories']['tleilaxu_tanks']['whole'][leader]
        self._object_state['hidden']['leaders'][faction].append(leader)
        cmd = '/{0} {1}'.format('reviveLeader', leader)
        self.appendCMD(cmd)

    def revive(self, caller_faction, n, troop_type):
        owner_faction = self.processor.manager.getFactionFromTroopType(troop_type)
        if owner_faction is None:
            raise ValueError('Unrecognized troop type: ' + troop_type)
        if 'tleilaxu_tanks' not in self._object_state['territories'].keys():
            raise ValueError('Troops not in Tleilaxu Tanks')
        if 'whole' not in self._object_state['territories']['tleilaxu_tanks'].keys():
            raise ValueError('Troops not in Tleilaxu Tanks')
        if troop_type not in self._object_state['territories']['tleilaxu_tanks']['whole'].keys():
            raise ValueError('Troops not in Tleilaxu Tanks')
        if self._object_state['territories']['tleilaxu_tanks']['whole'][troop_type] < n:
            raise ValueError('Not enough troops in Tleilaxu Tanks')
        self._object_state['territories']['tleilaxu_tanks']['whole'][troop_type] -= n
        if self._object_state['territories']['tleilaxu_tanks']['whole'][troop_type] == 0:
            del self._object_state['territories']['tleilaxu_tanks']['whole'][troop_type]
        self._object_state['hidden']['reserves'][owner_faction][troop_type] += n
        cmd = '/{0} {1} {2}'.format('revive', str(n), troop_type)
        self.appendCMD(cmd)

    def lead(self, faction, leader):
        participants = [
            self._object_state['territories']['wheel_attacker_player'],
            self._object_state['territories']['wheel_defender_player']
        ]
        if faction not in participants:
            raise ValueError('Player is not a battle participant')
        if not self.processor.manager.isLeader(leader):
            raise ValueError('Invalid leader')
        if faction == participants[0]:
            self._object_state['territories']['wheel_attacker_leader'] = leader
        if faction == participants[1]:
            self._object_state['territories']['wheel_defender_leader'] = leader

    def treachery(self, faction, card_type, card):
        print('treachery', card_type, card)
        participants = [
            self._object_state['territories']['wheel_attacker_player'],
            self._object_state['territories']['wheel_defender_player']
        ]
        if faction not in participants:
            raise ValueError('Player is not a battle participant')
        if card_type not in self._object_state['hidden']['cards'][faction].keys():
            raise ValueError('Player does not have that card in the hand')
        if card not in self._object_state['hidden']['cards'][faction][card_type]:
            raise ValueError('Player does not have that card in the hand')
        if card in self._object_state['hidden']['cards'][faction][card_type]:
            self._object_state['hidden']['cards'][faction][card_type].remove(card)
        if faction == participants[0]:
            if card_type not in self._object_state['territories']['wheel_attacker_cards'].keys():
                self._object_state['territories']['wheel_attacker_cards'][card_type] = []
            self._object_state['territories']['wheel_attacker_cards'][card_type] += [card]
        if faction == participants[1]:
            if card_type not in self._object_state['territories']['wheel_defender_cards'].keys():
                self._object_state['territories']['wheel_defender_cards'][card_type] = []
            self._object_state['territories']['wheel_defender_cards'][card_type] += [card]

    def reverseTreachery(self, faction, card_type, card):
        print('rev-treachery', card_type, card)
        participants = [
            self._object_state['territories']['wheel_attacker_player'],
            self._object_state['territories']['wheel_defender_player']
        ]
        if faction not in participants:
            raise ValueError('Player is not a battle participant')
        key = 'wheel_attacker_cards'
        if faction == participants[1]:
            key = 'wheel_defender_cards'
        if card not in self._object_state['territories'][key][card_type]:
            raise ValueError('This card is not part of the battle plan')
        self._object_state['territories'][key][card_type].remove(card)
        self._object_state['hidden']['cards'][faction][card_type].append(card)

    def discard(self, faction, card_type, card):
        participants = [
            self._object_state['territories']['wheel_attacker_player'],
            self._object_state['territories']['wheel_defender_player']
        ]
        if faction not in participants:
            raise ValueError('Player is not a battle participant')
        key = 'wheel_attacker_cards'
        if faction == participants[1]:
            key = 'wheel_defender_cards'
        if card not in self._object_state['territories'][key][card_type]:
            raise ValueError('This card is not part of the battle plan')
        self._object_state['territories'][key][card_type].remove(card)
        if card_type not in self._object_state['hidden']['discarded'].keys():
            self._object_state['hidden']['discarded'][card_type] = []
        self._object_state['hidden']['discarded'][card_type].append(card)
        cmd = '/{0} {1} {2}'.format('discard', faction, card)
        self.appendCMD(cmd)

    def discardHand(self, faction, card_type, card):
        if faction not in self._object_state['hidden']['reserves'].keys():
            raise ValueError('Incorrect faction')
        if card_type not in self._object_state['hidden']['cards'][faction].keys():
            raise ValueError('Player does not have that card in the hand')
        if card in self._object_state['hidden']['cards'][faction][card_type]: self._object_state['hidden']['cards'][faction][card_type].remove(card)
        if card_type not in self._object_state['hidden']['discarded'].keys():
            self._object_state['hidden']['discarded'][card_type] = []
        self._object_state['hidden']['discarded'][card_type].append(card)
        cmd = '/{0} {1} {2}'.format('discard', faction, card)
        self.appendCMD(cmd)

    def takeback(self, faction):
        participants = [
            self._object_state['territories']['wheel_attacker_player'],
            self._object_state['territories']['wheel_defender_player']
        ]
        if faction not in participants:
            raise ValueError('Player is not a battle participant')
        key = 'wheel_attacker_cards'
        if faction == participants[1]:
            key = 'wheel_defender_cards'
        for card_type, card_list in self._object_state['territories'][key].items():
            if card_type not in self._object_state['hidden']['cards'][faction].keys():
                self._object_state['hidden']['cards'][faction][card_type] = []
            for card in card_list:
                self._object_state['hidden']['cards'][faction][card_type].append(card)
        self._object_state['territories'][key] = []
        cmd = '/{0} {1}'.format('takeback', faction)
        self.appendCMD(cmd)

    def traitor(self, caller_faction, leader):
        # check if caller has a traitor card for this leader
        if 'traitor_' + leader not in self._object_state['hidden']['cards'][caller_faction]:
            raise ValueError('Player does not have this traitor')
        return True

    def battle(self, aggressor_faction, defender_faction):
        self._object_state['territories']['wheel_attacker_player'] = aggressor_faction
        self._object_state['territories']['wheel_defender_player'] = defender_faction
        self._object_state['territories']['wheel_attacker_cards'] = {}
        self._object_state['territories']['wheel_defender_cards'] = {}
        self._object_state['territories']['wheel_attacker_value'] = 0
        self._object_state['territories']['wheel_defender_value'] = 0
        self._object_state['territories']['wheel_attacker_leader'] = None
        self._object_state['territories']['wheel_defender_leader'] = None
        cmd = '/{0} {1} {2}'.format('battle', aggressor_faction, defender_faction)
        self.appendCMD(cmd)

    def deployment(self, faction, N):
        participants = [
            self._object_state['territories']['wheel_attacker_player'],
            self._object_state['territories']['wheel_defender_player']
        ]
        key = 'wheel_attacker_value'
        if faction == participants[1]:
            key = 'wheel_defender_value'
        self._object_state['territories'][key] = N

    def storm(self, sector):
        if sector[0] != 'S':
            raise ValueError('Invalid sector')
        position_str = sector[1:]
        try:
            position = int(position_str)
        except:
            raise ValueError('Invalid sector')
        self._object_state['territories']['storm'] = position
        cmd = '/{0} {1}'.format('storm', sector)
        self.appendCMD(cmd)

    def peek(self, faction, deck):
        if deck not in self._object_state['hidden']['decks'].keys():
            raise ValueError('Invalid deck name')
        cmd = '/{0} {1} {2}'.format('peek', faction, deck)
        self.appendCMD(cmd)
        card_id = self._object_state['hidden']['decks'][deck][0]
        card = self.cards_manager.card_objects[card_id]
        game_id = self._object_state['meta']['texts']['game_id']
        return game_id, card

    def draw(self, faction, deck):
        if deck not in self._object_state['hidden']['decks'].keys():
            raise ValueError('Invalid deck name')
        cmd = '/{0} {1} {2}'.format('draw', faction, deck)
        self.appendCMD(cmd)
        card_id = self._object_state['hidden']['decks'][deck].pop()
        if deck not in self._object_state['hidden']['cards'][faction].keys():
            self._object_state['hidden']['cards'][faction][deck] = []
        self._object_state['hidden']['cards'][faction][deck].append(card_id)
        card = self.cards_manager.card_objects[card_id]
        game_id = self._object_state['meta']['texts']['game_id']
        return game_id, card

    def hand(self, faction):
        leaders_list = self._object_state['hidden']['leaders'][faction]
        leaders_data = self.processor.manager.getLeadersNamesStrength(leaders_list)
        return {
            'game_id': self._object_state['meta']['texts']['game_id'],
            'faction_name': self.processor.game_config['faction_names'][faction],
            'cards': self._object_state['hidden']['cards'][faction],
            'spice': self._object_state['hidden']['spice'][faction],
            'reserves': self._object_state['hidden']['reserves'][faction],
            'leaders': leaders_data
        }

    def join(self, seat, username, player_id, faction='random'):
        if len(self._object_state['meta']['usernames'].keys()) >= 6:
            raise ValueError('too many players at the table')
        if seat not in list(range(1, 7)):
            raise ValueError('seat should be an integer between 1 and 6')
        key = 'player_{0}'.format(str(seat))
        self._object_state['meta']['usernames'][key] = username
        self._object_state['meta']['user_ids'][key] = player_id
        used = []
        for _, value in self._object_state['meta']['factions'].items():
            used.append(value)
        if faction in used:
            raise ValueError('this faction is already taken')
        if faction == 'random':
            available = []
            all_factions = ['atreides', 'bene_gesserit', 'emperor', 'spacing_guild', 'fremen', 'harkonnen']
            for f in all_factions:
                if f not in used:
                    available.append(f)
            faction = random.choice(available)
        self._object_state['meta']['factions'][key] = faction
        # print()
        # print(seat, username, player_id, faction, key)
        # print(self._object_state['meta']['factions'])
        # print()
        cmd = '/{0} {1} {2} {3}'.format('join', seat, username, player_id)
        if faction is not 'random':
            cmd += ' ' + faction
        self.appendCMD(cmd)

    def randomize(self, what):
        if what == 'factions':
            used = []
            for key, value in self._object_state['meta']['factions'].items():
                used.append(value)
            random.shuffle(used)
            for key, f in zip(self._object_state['meta']['factions'].keys(), used):
                self._object_state['meta']['factions'][key] = f
            # print('randomized')
            # print(self._object_state['meta']['factions'])
            self.appendCMD('/randomize factions')

    def config(self, key, param1, param2):
        # TODO validation?
        params = [param1, param2]
        self._object_state['configs'][key] = params
        args = ['configs', key]
        cmd = '/' + 'configs'
        if param1 is not None:
            cmd += ' ' + str(param1)
        if param2 is not None:
            cmd += ' ' + str(param2)
        self.appendCMD(cmd)

    def appendCMD(self, cmd):
        self._object_state['hidden']['height'] += 1
        height = self._object_state['hidden']['height']
        self._object_state['meta']['texts']['commands'].append(str(height) + ' ' + cmd)
        if len(self._object_state['meta']['texts']['commands']) > 8:
            del self._object_state['meta']['texts']['commands'][0]
        # print(self._object_state['meta']['texts'])

    def shieldWallDestroyed(self, state: bool):
        self._object_state['meta']['shield_wall_destroyed'] = state
        self.appendCMD('/shield_wall {0}'.format(str(state)))

    def initgame(self):
        deck_treachery = list(self.cards_manager.headers_deck_treachery)
        deck_spice = list(self.cards_manager.headers_deck_spice)
        deck_storm = list(self.cards_manager.headers_deck_storm)
        deck_traitor = list(self.cards_manager.headers_deck_traitor)
        random.shuffle(deck_treachery)
        random.shuffle(deck_spice)
        random.shuffle(deck_storm)
        random.shuffle(deck_traitor)
        meta = self._object_state['meta']
        hidden = self._object_state['hidden']
        hidden['decks'] = {
            'treachery': deck_treachery,
            'spice': deck_spice,
            'storm': deck_storm,
            'traitor': deck_traitor
        }
        hidden['leaders'] = {}
        territories = {
            'storm': random.randint(1, 18)
        }
        for player, faction in meta['factions'].items():
            hidden['cards'][faction] = {}
            hidden['leaders'][faction] = self.processor.manager.getLeaders(faction)
            if faction == 'atreides':
                hidden['reserves']['atreides'] = {
                    'atreides_troops': 10
                }
                hidden['spice']['atreides'] = 10
                territories['arrakeen'] = {
                    'S10': {
                        'atreides_troops': 10
                    }
                }
            if faction == 'harkonnen':
                hidden['reserves']['harkonnen'] = {
                    'harkonnen_troops': 10
                }
                hidden['spice']['harkonnen'] = 10
                territories['carthag'] = {
                    'S11': {
                        'harkonnen_troops': 10
                    }
                }
            if faction == 'emperor':
                hidden['reserves']['emperor'] = {
                    'emperor_troops': 15,
                    'sardaukar': 5
                }
                hidden['spice']['emperor'] = 10
            if faction == 'bene_gesserit':
                hidden['reserves']['bene_gesserit'] = {
                    'bene_gesserit_troops': 19
                }
                hidden['spice']['bene_gesserit'] = 5
                territories['polar_sink'] = {
                    'whole': {
                        'bene_gesserit_troops': 1
                    }
                }
            if faction == 'spacing_guild':
                hidden['reserves']['spacing_guild'] = {
                    'spacing_guild_troops': 15
                }
                hidden['spice']['spacing_guild'] = 5
                territories['tueks_sietch'] = {
                    'S5': {
                        'spacing_guild_troops': 5
                    }
                }
            if faction == 'fremen':
                hidden['reserves']['fremen'] = {
                    'fremen_troops': 7,
                    'fedaykin': 3
                }
                hidden['spice']['fremen'] = 3
                a = random.randint(0, 7)
                b = random.randint(0, 7-a)
                c = random.randint(0, 7-a-b)
                territories['sietch_tabr'] = {
                    'S14': {
                        'fremen_troops': 1 + a
                    }
                }
                territories['false_wall_south'] = {
                    'S4': {
                        'fremen_troops': 1 + b
                    }
                }
                territories['false_wall_west'] = {
                    'S18': {
                        'fremen_troops': 1 + c
                    }
                }
        self._object_state['hidden'] = hidden
        self._object_state['territories'] = territories
        self.appendCMD('/init')


    def initiate(self, meta):
        hidden = {
            'reserves': {},
            'spice': {},
            'battle': {
                'aggressor': None,
                'defender': None
            },
            'cards': {},
            'discarded': {},
            'height': 0,
            'decks': {}
        }
        _object_state = {
            'hidden': hidden,
            'territories': {},
            'visual': {},
            'meta': meta,
            'configs': {}
        }
        return _object_state

    def render(self, outfile, battle=False):
       self._object_state = self.processor.process(self._object_state)
       renderer = Renderer(
           self._object_state,
           self.processor.game_config,
           self.cards_manager.card_objects,
           outfile,
           battle=battle)
       renderer.render()
