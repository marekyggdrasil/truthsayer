import random
import math
import pareto

from itertools import compress

from bs4 import BeautifulSoup

from shapely.geometry import Polygon, LineString
from shapely.affinity import translate
from shapely.geometry.point import Point

from simpleai.search import SearchProblem
from simpleai.search.traditional import greedy
from simpleai.search.local import beam, genetic, hill_climbing_stochastic, simulated_annealing

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


def generate_random(number, polygon, tolerance=0.1, target_radius=None, centroid=False):
    points = []
    # print(polygon.bounds)
    minx, miny, maxx, maxy = polygon.bounds
    while len(points) < number:
        pnt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if target_radius is not None:
            pnt.buffer(target_radius)
        if polygon.contains(pnt):
            if target_radius is not None:
                pnt_area = math.pi*(target_radius**2)
                ratio = polygon.intersection(pnt).area/pnt_area
                if ratio < pnt.area*(1-tolerance):
                    diffx = (pnt.x-centroid.x)
                    diffy = (pnt.y-centroid.y)
                    m = diffy/diffx
                    x = pnt.x+ratio*diffx
                    pnt2 = Point(x, m*x+centroid.y)
                    pnt2.buffer(target_radius)
                    points.append(pnt2)
                else:
                    points.append(pnt)
            else:
                points.append(pnt)
    # print(len(points))
    if len(points) == 0:
        pnt = polygon.centrod
        if target_radius is not None:
            pnt.buffer(target_radius)
        return [pnt]
    # print(points[0])
    return points


def grid_solver(grad, target_radius, polygon, polygons_avoid, tolerance_covering=0.8, tolerance_collision=0.1, max_sols=5):
    minx, miny, maxx, maxy = polygon.bounds
    x_res = list(range(int((maxx-minx-target_radius/2)/grad)))
    y_res = list(range(int((maxy-miny-target_radius/2)/grad)))
    random.shuffle(x_res)
    random.shuffle(y_res)
    best_covering = 0
    best_collisions = float('inf')
    solutions = []
    solutions_candidates = []
    for x_idx in x_res:
        for y_idx in y_res:
            x_cor = minx + grad*x_idx + target_radius/2
            y_cor = miny + grad*y_idx + target_radius/2
            candidate = Point(x_cor, y_cor).buffer(target_radius)
            area_covering = polygon.intersection(candidate).area
            if area_covering < tolerance_covering*candidate.area:
                continue
            area_collision = 0
            for avoid in polygons_avoid:
                area_collision += avoid.intersection(candidate).area
            if area_collision > tolerance_collision*candidate.area:
                continue
            solutions.append(tuple([area_covering, area_collision]))
            solutions_candidates.append(tuple([x_cor, y_cor]))
            if len(solutions_candidates) == max_sols:
                break
        else:
            continue  # only executed if the inner loop did NOT break
        break  # only executed if the inner loop DID break
    if len(solutions) == 0:
        return []
    nondominated = pareto.flag_nondominated(solutions, objectives=[0, 1], maximize=[0])
    nondominated_indices = list(compress(range(len(nondominated)), nondominated))
    nondominated_candidates = [solutions_candidates[j] for j in nondominated_indices]
    return nondominated_candidates


class TokenPlacementProblem(SearchProblem):
    def __init__(self, polygons_maximize_overlap, polygons_avoid_overlap_areas, target_radius, tolerance=0.1, initial_state=None):
        self.polygons_maximize_overlap = polygons_maximize_overlap
        self.polygons_avoid_overlap_areas = polygons_avoid_overlap_areas
        self.target_radius = target_radius
        self.tolerance = tolerance
        if initial_state is None:
            initial_state = self.generate_random_state()
        super().__init__(initial_state=initial_state)

    def actions(self, state):
        possible_actions = []
        state_polygon = self.polygonize(state)
        centroid = self.polygons_maximize_overlap.centroid
        ox, oy = centroid.x, centroid.y
        px, py = state
        angles = [math.pi*i/12 for i in range(1, 25)]
        rotations = [
            tuple([math.cos(angle)*(px-ox)-math.sin(angle)*(py-oy), math.sin(angle)*(px-ox)+math.cos(angle)*(py-oy)]) for angle in angles]
        if px-ox > 1:
            m = (py-oy)/(px-ox)
            trs = [-60, -40, -20, -10, -5, 5, 10, 20, 40, 60]
            translations = [(x, m*x+oy) for x in trs]
            return rotations + translations
        return rotations

    def result(self, state, action):
        xoff, yoff = action
        centroid = self.polygons_maximize_overlap.centroid
        x, y = centroid.x, centroid.y
        return x+xoff, y+yoff

    def polygonize(self, state):
        x, y = state
        state_center = Point(x, y)
        return state_center.buffer(self.target_radius)

    def heuristic(self, state):
        # how far are we from the goal?
        bad = 0
        state_polygon = self.polygonize(state)
        for avoid in self.polygons_avoid_overlap_areas:
            area = state_polygon.intersection(avoid).area
            bad += area**3
        overlap = (state_polygon.intersection(self.polygons_maximize_overlap).area)
        if overlap < state_polygon.area - self.tolerance:
            centroid = self.polygons_maximize_overlap.centroid
            px, py = state
            ox, oy = centroid.x, centroid.y
            bad += ((px - ox)**2 + (py - oy)**2)**5
        else:
            bad -= overlap
        return bad

    def crossover(self, state1, state2):
        x1, y1 = state1
        x2, y2 = state2
        rnd = random.random()
        if rnd < 0.5:
            return x1, y2
        else:
            return x2, y1

    def mutate(self, state):
        # cross both strings, at a random point
        actions = self.actions(state)
        action = random.sample(actions, 1)[0]
        mutated = self.result(state, action)
        return mutated

    def generate_random_state(self):
        state_center = generate_random(1, self.polygons_maximize_overlap, centroid=True)[0]
        state = state_center.x, state_center.y
        return state

    def value(self, state):
        # how good is this state?
        return -self.heuristic(state)


def howbad(state_polygon, polygons_maximize_overlap, polygons_avoid_overlap_areas, tolerance=0.1):
    # how far are we from the goal?
    bad = 0
    for avoid in polygons_avoid_overlap_areas:
        area = state_polygon.intersection(avoid).area
        bad += area
    return bad

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
        # polygons_maximize_overlap.difference(polygon_avoid_leader)
    for x, y in avoid_tokens:
        center = Point(x, y)
        polygon_avoid_token = center.buffer(radius_token)
        avoid_overlap_areas.append(polygon_avoid_token)
        # polygons_maximize_overlap.difference(polygon_avoid_token)
    for x, y in avoid_spice:
        center = Point(x, y)
        polygon_avoid_spice = center.buffer(radius_spice)
        avoid_overlap_areas.append(polygon_avoid_spice)
        # polygons_maximize_overlap.difference(polygon_avoid_spice)
    for coords in avoid_zones:
        zone = Polygon(coords)
        avoid_overlap_areas.append(zone)
        # polygons_maximize_overlap = polygons_maximize_overlap.difference(zone)
    '''
    for tolerance_covering in [0.9, 0.8, 0.7, 0.6, 0.5]:
        for tolerance_collision in [0.1, 0.2, 0.3, 0.4, 0.5]:
            candidates = grid_solver(5, target_radius, polygons_maximize_overlap, avoid_overlap_areas)
            if len(candidates) > 0:
                candidate = random.sample(candidates, 1)[0]
                return candidate
    '''
    '''
    best = float('inf')
    best_candidate = None
    for i in range(2000):
        candidate_polygon = generate_random(1, polygons_maximize_overlap, target_radius=target_radius, tolerance=0.9, centroid=True)[0]
        bad = howbad(candidate_polygon, polygons_maximize_overlap, avoid_overlap_areas, tolerance=0.0)
        if bad < best:
            best_candidate = candidate_polygon
    return best_candidate.centroid.x, best_candidate.centroid.y
    '''
    # state = state_center.buffer(target_radius)
    # solve it
    problem = TokenPlacementProblem(polygons_maximize_overlap, avoid_overlap_areas, target_radius, tolerance=0.01)
    # return problem.generate_random_state()
    # result = greedy(problem, graph_search=False, viewer=None)
    # result = beam(problem, beam_size=20, iterations_limit=20)
    result = genetic(problem, population_size=75, mutation_chance=0.15, iterations_limit=120)
    # result = simulated_annealing(problem, iterations_limit=120)
    # result = hill_climbing_stochastic(problem, iterations_limit=120)
    # solution = result.state
    # centroid = solution.centroid
    # return tuple([centroid.x, centroid.y])
    return result.state
