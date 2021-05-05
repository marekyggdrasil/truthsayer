from bs4 import BeautifulSoup
from shapely.geometry import Polygon, LineString

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


def getRegionsLocations(areas):
    regions = []
    locations = []
    for r in areas['polygons'].keys():
        if r[0] == 'R':
            regions.append(r)
        else:
            locations.append(r)
    return regions, locations


def findIntersections(areas, regions, locations):
    locs = {}
    for region in regions:
        region_coords = areas['polygons'][region]
        region_polygon = Polygon(region_coords)
        for location in locations:
            location_coords = areas['polygons'][location]
            location_polygon = Polygon(location_coords)
            if region_polygon.intersects(location_polygon):
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
