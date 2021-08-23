import json

from truthsayer.poly import extract, getRegionsLocations, findNeighboring, findIntersections, findStorm

areas = extract()
regions, locations = getRegionsLocations(areas)
location_regions = findIntersections(areas, regions, locations)
neighbors = findNeighboring(areas, regions, locations, skip=['arrakis', 'tleilaxu_tanks'])

cx, cy, r = findStorm(areas)

filename = 'truthsayer/assets/game_config.json'

game_config = None
with open(filename) as json_file:
    game_config = json.load(json_file)

game_config['generated'] = {
    'territories': areas,
    'regions': regions,
    'locations': locations,
    'location_regions': location_regions,
    'neighbors': neighbors,
    'map_center': {
        'x': cx,
        'y': cy,
        'r': r
    }
}

with open(filename, 'w') as outfile:
    json.dump(game_config, outfile)
