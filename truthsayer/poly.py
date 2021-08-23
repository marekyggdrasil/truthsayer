import random
import math
import pareto

from itertools import compress

from bs4 import BeautifulSoup

from shapely.geometry import Polygon, LineString
from shapely.affinity import translate
from shapely.geometry.point import Point

from simpleai.search.local import genetic

try:
    import importlib.resources as pkg_resources
except ImportError:
    # Try backported to PY<37 `importlib_resources`.
    import importlib_resources as pkg_resources

from truthsayer import assets

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
    sectors = []
    locations = []
    for r in areas['polygons'].keys():
        if locations not in skip:
            if r[0] == 'R':
                r[0] = 'S'
            if r[0] == 'S':
                sectors.append(r)
            else:
                locations.append(r)
    return sectors, locations


def findIntersections(areas, sectors, locations, threshold=400):
    locs = {}
    for sector in sectors:
        sector_coords = areas['polygons'][sector]
        sector_polygon = Polygon(sector_coords)
        for location in locations:
            location_coords = areas['polygons'][location]
            location_polygon = Polygon(location_coords)
            if sector_polygon.intersection(location_polygon).area > threshold:
                if location not in locs.keys():
                    locs[location] = []
                locs[location].append(sector)
                locs[location] = list(set(locs[location]))
    return locs


def findNeighboring(areas, sectors, locations, skip=[]):
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


def findStorm(areas):
    centers, xs, ys = [], 0, 0
    for i in range(1, 7):
        key = 'player_{0}'.format(str(i))
        player = areas['circles'][key]
        x, y = player
        centers.append(player)
        xs += x
        ys += y
    cx, cy = xs/6, ys/6
    r = 0
    for x, y in centers:
        r += math.sqrt((cx-x)**2+(cy-y)**2)
    r /= 6
    return cx, cy, r


def generate_random(number, polygon, centroid=False):
    points = []
    minx, miny, maxx, maxy = polygon.bounds
    while len(points) < number:
        pnt = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        if polygon.contains(pnt):
            points.append(pnt)
    if len(points) == 0:
        pnt = polygon.centrod
        return [pnt]
    return points


'''
def placeToken(
        areas,
        locations,
        location_sectors,
        target_location,
        target_radius,
        target_sector=None,
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
    if target_sector is not None:
        polygons_sector = Polygon(areas['polygons'][target_sector])
        polygons_maximize_overlap = polygons_maximize_overlap.intersection(polygons_sector)
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
    problem = TokenPlacementProblem(polygons_maximize_overlap, avoid_overlap_areas, target_radius, tolerance=0.01)
    result = genetic(problem, population_size=75, mutation_chance=0.15, iterations_limit=120)
    return result.state
'''
