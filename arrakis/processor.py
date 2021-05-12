from shapely.geometry import Polygon
from shapely.geometry.point import Point

from opti import TokenPlacementProblem
from opti import MultiTokenPlacementProblem


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
        game_state['visual'][area_name][region_name][element] = x, y
    return result.state


def process(game_state, game_config, all_areas=[], point_areas=[]):
    # find objects which should be rendered but have no coordinates
    to_place = {}
    for area in all_areas:
        if area in game_state['areas'].keys():
            if area not in game_state['visual'].keys():
                game_state['visual'][area] = {}
            for region in game_state['areas'][area].keys():
                for token in game_state['areas'][area][region].keys():
                    if token not in game_state['visual'][area].keys():
                        if area in point_areas:
                            x, y = point_areas[area]
                            game_state['visual'][area][region][token] = x, y
                            continue
                        if area not in to_place:
                            to_place[area] = {}
                        if region not in to_place[area].keys():
                            to_place[area][region] = []
                        to_place[area][region].append(token)
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
    for area in game_state['visual'].keys():
        for token in game_state['visual'][area]:
            if token not in game_state['areas'][area].keys():
                removal = area, token
                to_remove.append(removal)
    # remove gathered
    for area, token in to_remove:
        del game_state['visual'][area][token]
    return game_state
