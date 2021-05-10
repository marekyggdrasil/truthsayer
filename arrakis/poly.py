import random
import math

from bs4 import BeautifulSoup

from shapely.geometry import Polygon, LineString
from shapely.affinity import translate
from shapely.geometry.point import Point

from simpleai.search import SearchProblem
from simpleai.search.traditional import greedy
from simpleai.search.local import beam, genetic, simulated_annealing

from KnapsackPacking.problem_solution import Item, Container, Problem, Solution
from KnapsackPacking.shape_functions import get_bounding_rectangle_center

import KnapsackPacking.evolutionary as evolutionary

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

from arrakis import assets


def extract():
    coordinates_file = pkg_resources.read_text(assets, 'arrakis.html')
    soup = BeautifulSoup(coordinates_file, 'html.parser')
    areas = {
        'circles': {},
        'polygons': {}
    }
    for area in soup.find_all('area'):
        name = area.get('title')
        shape = area.get('shape')
        coords = area.get('coords').split(',')
        coords = [int(c) for c in coords]
        if shape == 'poly':
            edges = []
            for j in range(int(len(coords)/2)):
                jx = 2*j
                jy = 2*j+1
                xy = tuple([coords[jx], coords[jy]])
                edges.append(xy)
            areas['polygons'][name] = edges
        elif shape == 'circle':
            x = coords[0]
            y = coords[1]
            center = tuple([x, y])
            areas['circles'][name] = center
    return areas


def getRegionsLocations(areas, skip=[]):
    regions = []
    locations = []
    for r in areas['polygons'].keys():
        if locations not in skip:
            if r[0] == 'R':
                regions.append(r)
            else:
                locations.append(r)
    return regions, locations


def findIntersections(areas, regions, locations, threshold=400):
    locs = {}
    for region in regions:
        region_coords = areas['polygons'][region]
        region_polygon = Polygon(region_coords)
        for location in locations:
            location_coords = areas['polygons'][location]
            location_polygon = Polygon(location_coords)
            if region_polygon.intersection(location_polygon).area > threshold:
                if location not in locs.keys():
                    locs[location] = []
                locs[location].append(region)
                locs[location] = list(set(locs[location]))
    return locs


def findNeighboring(areas, regions, locations, skip=[]):
    neighbors = []
    for i in range(len(locations)):
        loc1 = locations[i]
        if loc1 not in skip:
            loc1_coords = areas['polygons'][loc1]
            loc1_polygon = Polygon(loc1_coords)
            for j in range(i+1, len(locations)):
                loc2 = locations[j]
                if loc2 not in skip:
                    loc2_coords = areas['polygons'][loc2]
                    loc2_polygon = Polygon(loc2_coords)
                    if loc1_polygon.intersects(loc2_polygon):
                        neighbors.append(tuple([loc1, loc2]))
    return neighbors


def findCenters(areas, locations, skip=[]):
    centers = {}
    for location in locations:
        if location not in skip:
            location_coords = areas['polygons'][location]
            location_polygon = Polygon(location_coords)
            centroid = location_polygon.centroid
            centers[location] = tuple([centroid.x, centroid.y])
    return centers


def generate_random(number, polygon, centroid=False):
    points = []
    minx, miny, maxx, maxy = polygon.bounds
    while len(points) < number:
        pnt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(pnt):
            points.append(pnt)
    if len(points) == 0:
        return [polygon.centroid]
    return points


class TokenPlacementProblem(SearchProblem):
    def __init__(self, polygons_maximize_overlap, polygons_avoid_overlap_areas, target_radius, tolerance=0.1, initial_state=None):
        self.polygons_maximize_overlap = polygons_maximize_overlap
        self.polygons_avoid_overlap_areas = polygons_avoid_overlap_areas
        self.target_radius = target_radius
        self.tolerance = tolerance
        super().__init__(initial_state=initial_state)

    def actions(self, state):
        possible_actions = []
        state_polygon = self.polygonize(state)
        if state_polygon.intersects(self.polygons_maximize_overlap):
            return list([(-5, -5), (-5, 0), (0, -5), (5, 5), (5, 0), (0, 5)])
        else:
            return []

    def result(self, state, action):
        xoff, yoff = action
        x, y = state
        # state_center = Point(x, y)
        # state_polygon = state_center.buffer(self.target_radius)
        # translated = translate(state, xoff=xoff, yoff=yoff, zoff=0.0)
        return x+xoff, y+yoff

    def polygonize(self, state):
        x, y = state
        state_center = Point(x, y)
        return state_center.buffer(self.target_radius)

    def is_goal(self, state):
        state_polygon = self.polygonize(state)
        for avoid in self.polygons_avoid_overlap_areas:
            if state_polygon.intersection(avoid).area > self.tolerance:
                return False
        return True

    def cost(self, state, action, state2):
        return 1

    def heuristic(self, state):
        # how far are we from the goal?
        bad = 0
        state_polygon = self.polygonize(state)
        for avoid in self.polygons_avoid_overlap_areas:
            area = state_polygon.intersection(avoid).area
            if area > self.tolerance:
                bad += area**2
        bad -= state_polygon.intersection(self.polygons_maximize_overlap).area
        return bad

    def crossover(self, state1, state2):
        x1, y1 = state1
        x2, y2 = state2
        xc, yc = (x1+x2)/2, (y1+y2)/2
        child = xc, yc
        return child

    def mutate(self, state):
        # cross both strings, at a random point
        x, y = state
        xm = x + random.randint(0, 10)
        ym = y + random.randint(0, 10)
        mutated = xm, ym
        return mutated

    def generate_random_state(self):
        state_center = generate_random(1, self.polygons_maximize_overlap, centroid=True)[0]
        state = state_center.x, state_center.y
        return state

    def value(self, state):
        # how good is this state?
        return -self.heuristic(state)

def placeToken(
        areas,
        locations,
        location_regions,
        target_location,
        target_radius,
        target_region=None,
        background=None,
        avoid_leaders=[],
        avoid_tokens=[],
        avoid_spice=[],
        avoid_zones=[],
        radius_leader=90,
        radius_token=46,
        radius_spice=46,
        w=1000,
        h=1000):
    polygons_maximize_overlap = Polygon(areas['polygons'][target_location])
    if target_region is not None:
        polygons_region = Polygon(areas['polygons'][target_region])
        polygons_maximize_overlap = polygons_maximize_overlap.intersection(polygons_region)
    avoid_overlap_areas = []
    if background is not None:
        back = Polygon(background)
        difference = back.difference(polygons_maximize_overlap)
        avoid_overlap_areas.append(difference)
    for x, y in avoid_leaders:
        center = Point(x, y)
        polygon_avoid_leader = center.buffer(radius_leader)
        avoid_overlap_areas.append(polygon_avoid_leader)
    for x, y in avoid_tokens:
        center = Point(x, y)
        polygon_avoid_token = center.buffer(radius_token)
        avoid_overlap_areas.append(polygon_avoid_token)
    for x, y in avoid_spice:
        center = Point(x, y)
        polygon_avoid_spice = center.buffer(radius_spice)
        avoid_overlap_areas.append(polygon_avoid_spice)
    for coords in avoid_zones:
        zone = Polygon(coords)
        avoid_overlap_areas.append(zone)
    # outside regions
    tw = 2*target_radius
    th = 2*target_radius
    avoid_overlap_areas.append(Polygon(
        [(-tw, 0), (0, 0), (0, h+th), (-tw, h+th)]))
    avoid_overlap_areas.append(Polygon(
        [(0, h), (w+tw, h), (w+tw, h+th), (0, h+th)]))
    avoid_overlap_areas.append(Polygon(
        [(w, -th), (w+tw, -th), (w+tw, h), (w, h)]))
    avoid_overlap_areas.append(Polygon(
        [(-tw, -th), (w, -th), (w, 0), (-tw, 0)]))
    state_center = generate_random(1, polygons_maximize_overlap, centroid=True)[0]
    state = state_center.x, state_center.y
    # state = state_center.buffer(target_radius)
    # solve it
    problem = TokenPlacementProblem(polygons_maximize_overlap, avoid_overlap_areas, target_radius, tolerance=0.0, initial_state=state)
    # result = greedy(problem, graph_search=False, viewer=None)
    # result = beam(problem, beam_size=20, iterations_limit=20)
    # result = genetic(problem, population_size=200, mutation_chance=0.25, iterations_limit=5)
    result = simulated_annealing(problem, iterations_limit=400)
    # solution = result.state
    # centroid = solution.centroid
    # return tuple([centroid.x, centroid.y])
    return result.state


def placeTokenKnapsack(
        areas,
        locations,
        location_regions,
        target_locations,
        target_radii,
        target_region=None,
        background=None,
        avoid_leaders=[],
        avoid_tokens=[],
        avoid_spice=[],
        avoid_zones=[],
        radius_leader=90,
        radius_token=46,
        radius_spice=46,
        w=1000,
        h=1000):
    polygons_maximize_overlap = Polygon(areas['polygons'][target_locations[0]])
    centroid = polygons_maximize_overlap.centroid
    if target_region is not None:
        polygons_region = Polygon(areas['polygons'][target_region])
        polygons_maximize_overlap = polygons_maximize_overlap.intersection(polygons_region)
    max_weight = 120.
    container = Container(max_weight, polygons_maximize_overlap)
    items = [Item(Point(centroid.x, centroid.y).buffer(target_radius), 40., 50.) for target_radius in target_radii]
    problem = Problem(container, items)
    solution = evolutionary.solve_problem(problem)
    positions = []
    for key, value in solution.placed_items.items():
        shape_center = value.position
        positions.append(shape_center)
    print(positions)
    return positions
