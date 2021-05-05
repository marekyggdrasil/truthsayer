from bs4 import BeautifulSoup
from shapely.geometry import Polygon

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


def findIntersections(areas):
    regions = []
    locations = []
    for r in areas['polygons'].keys():
        if r[0] == 'R':
            regions.append(r)
        else:
            locations.append(r)
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
