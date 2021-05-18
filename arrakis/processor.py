import math

from shapely.geometry import Polygon
from shapely.geometry.point import Point

from arrakis.opti import TokenPlacementProblem
from arrakis.opti import MultiTokenPlacementProblem


def getRadius(game_config, element):
    diameter = None
    if element in game_config['static']['leader_tokens'].keys():
        diameter = game_config['static']['dimensions']['leader']
    elif element in game_config['static']['troop_tokens']:
        diameter = game_config['static']['dimensions']['troop']
    radius = diameter/2
    return radius


def prepareInstance(game_state, game_config, area_name, region_name):
    polygons_maximize_overlap = Polygon(game_config['generated']['polygons'][area_name])
    if region_name != 'whole':
        polygons_region = Polygon(areas['generated']['polygons'][region_name])
        polygons_maximize_overlap = polygons_maximize_overlap.intersection(polygons_region)
    avoid_overlap_areas = []
    if area_name not in game_state['visual'].keys():
        game_state['visual'][area_name] = {}
    if region_name not in game_state['visual'][area_name].keys():
        game_state['visual'][area_name][region_name] = {}
    for token_name in game_state['visual'][area_name][region_name].keys():
        x, y = game_state['visual'][area_name][region_name][token_name]
        radius = getRadius(game_config, token_name)
        polygon_token = Point(x, y).buffer(radius)
        avoid_overlap_areas.append(polygon_token)
    return polygons_maximize_overlap, avoid_overlap_areas


def placeSingleToken(game_state, game_config, area_name, region_name, element, tolerance=0.01):
    target_radius = getRadius(game_config, element)
    polygons_maximize_overlap, avoid_overlap_areas = prepareInstance(game_state, game_config, area_name, region_name)
    problem = TokenPlacementProblem(polygons_maximize_overlap, avoid_overlap_areas, target_radius, tolerance=0.01)
    result = genetic(problem, population_size=75, mutation_chance=0.15, iterations_limit=120)
    x, y = result.state
    game_state['visual'][area_name][region_name][element] = x, y
    return result.state


def placeMultipleTokens(game_state, area_name, region_name, elements):
    target_radii = [getRadius(game_config, element) for element in elements]
    polygons_maximize_overlap, avoid_overlap_areas = prepareInstance(game_state, game_config, area_name, region_name)
    problem = MultiTokenPlacementProblem(polygons_maximize_overlap, avoid_overlap_areas, target_radii, tolerance=0.01)
    result = genetic(problem, population_size=75, mutation_chance=0.15, iterations_limit=120)
    for i, element in enumerate(elements):
        x = result.state[i*2]
        y = result.state[i*2+1]
        token_object = {
            'token': element,
            'region': region_name,
            'x': x,
            'y': y
        }
        game_state['visual'][area_name][region_name][element] = token_object
    return result.state

def calculateStormPosition(game_config, position):
    cx = game_config['generated']['map_center']['x']
    cy = game_config['generated']['map_center']['y']
    cr = game_config['generated']['map_center']['r']+7
    angle = (position-6.5)*360/18
    angle_rot = angle - 90
    angle_rad = 2*math.pi*(-angle)/360
    x = cx+math.cos(angle_rad)*cr
    y = cy+math.sin(angle_rad)*cr
    storm_object = {
        'token': game_config['files']['storm'],
        'x': x,
        'y': y,
        's': 0.5,
        'a': angle_rot,
    }
    return storm_object

def calculateWheel(value):
    return 360*(value+1.25)/21

def process(game_state, game_config):
    # find objects which should be rendered but have no coordinates
    all_areas = list(game_config['generated']['areas']['circles'].keys())
    all_areas += list(game_config['generated']['areas']['polygons'].keys())
    all_areas = list(set(all_areas))
    to_place = {}
    for area in all_areas:
        if area in game_state['areas'].keys():
            if area not in game_state['visual'].keys():
                game_state['visual'][area] = {}
            if area in game_config['types']['areas']['point']:
                if area in game_config['types']['areas']['spice']:
                    value = game_state['areas'][area]
                    game_state['visual'][area] = value
                continue
            for region in game_state['areas'][area].keys():
                for token in game_state['areas'][area][region].keys():
                    if token not in game_state['visual'][area].keys():
                        if area not in to_place:
                            to_place[area] = {}
                        if region not in to_place[area].keys():
                            to_place[area][region] = []
                        to_place[area][region].append(token)
    if 'storm' in game_state['areas'].keys():
        position = game_state['areas']['storm']
        storm_object = calculateStormPosition(game_config, position)
        game_state['visual']['storm'] = storm_object
    for area, faction in game_state['meta']['factions'].items():
        faction_symbol = game_config['faction_symbols'][faction]
        file = game_config['files'][faction_symbol]
        print(faction, faction_symbol, file)
        game_state['visual'][area] = file
    wheel_values = ['wheel_attacker_value', 'wheel_defender_value']
    for wheel in wheel_values:
        if wheel in game_state['areas'].keys():
            value = game_state['areas'][wheel]
            game_state['visual'][wheel] = calculateWheel(value)
    wheel_leaders = ['wheel_attacker_leader', 'wheel_defender_leader']
    for wheel in wheel_leaders:
        if wheel in game_state['areas'].keys():
            leader = game_state['areas'][wheel]
            file = game_config['files'][leader]
            game_state['visual'][wheel] = file
    wheel_players = ['wheel_attacker_player', 'wheel_defender_player']
    wheel_players_refs = {}
    for wheel in wheel_players:
        if wheel in game_state['areas'].keys():
            player_key = game_state['areas'][wheel]
            faction_key = game_state['meta']['factions'][player_key]
            faction_name = game_config['faction_names'][faction_key]
            player_name = game_state['meta']['usernames'][player_key]
            game_state['visual'][wheel + '_faction'] = faction_name
            game_state['visual'][wheel + '_name'] = player_name
            wheel_players_refs[wheel + '_faction'] = wheel
            wheel_players_refs[wheel + '_name'] = wheel
    # optimize positions of tokens that need placement
    for area_name in to_place.keys():
        for region_name in to_place[area_name]:
            elements = to_place[area_name][region_name]
            if len(elements) == 1:
                element = elements[0]
                placeSingleToken(game_state, game_config, area_name, region_name, element)
                continue
            placeMultipleTokens(game_state, area_name, region_name, elements)
    # find objects which have coordinates but should be removed
    to_remove = []
    to_remove_points = []
    for area in game_state['visual'].keys():
        if area in game_config['types']['areas']['point']:
            if area in game_config['types']['areas']['players']:
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
        faction_name = game_config['faction_names'][faction_key]
        text = '{0}\n{1}'.format(player_name, faction_name)
        if 'texts' not in game_state['meta'].keys():
            game_state['meta']['texts'] = {}
        if 'usernames' not in game_state['meta']['texts'].keys():
            game_state['meta']['texts']['usernames'] = {}
        game_state['meta']['texts']['usernames'][player_key] = text
    return game_state
