import json

from truthsayer.poly import extract, getRegionsLocations, findNeighboring, findIntersections, findStorm

areas = extract()
regions, locations = getRegionsLocations(areas)
location_regions = findIntersections(areas, regions, locations, threshold=400)
neighbors = findNeighboring(areas, regions, locations, skip=['arrakis', 'tleilaxu_tanks'])

print()

neighborhoods = {}
for territory in locations:
    for sector in location_regions.get(territory, []):
        if territory not in neighborhoods.keys():
            neighborhoods[territory] = {}
        neighborhood = {}
        for entry in neighbors + [[territory, territory]]:
            neighbor_territory = None
            neighbor_territory_sectors = []
            if entry[0] == territory:
                neighbor_territory = entry[1]
            elif entry[1] == territory:
                neighbor_territory = entry[0]
            if neighbor_territory is None:
                continue
            if neighbor_territory not in neighborhood.keys():
                neighborhood[neighbor_territory] = []
            neighbor_sectors = location_regions.get(neighbor_territory, [])
            sm = 'S' + str(int(sector.replace('S', ''))-1)
            so = sector
            sp = 'S' + str(int(sector.replace('S', ''))+1)
            if sm in neighbor_sectors:
                neighbor_territory_sectors += [sm]
            if so in neighbor_sectors:
                neighbor_territory_sectors += [so]
            if sp in neighbor_sectors:
                neighbor_territory_sectors += [sp]
            if len(neighbor_territory_sectors) > 0:
                neighborhood[neighbor_territory] += neighbor_territory_sectors
                neighborhood[neighbor_territory] = list(set(neighborhood[neighbor_territory]))
        neighborhoods[territory][sector] = neighborhood

cx, cy, r = findStorm(areas)

filename = 'truthsayer/assets/game_config.json'

game_config = None
with open(filename) as json_file:
    game_config = json.load(json_file)

game_config['generated'] = {
    'territories': areas,
    'sectors': regions,
    'locations': locations,
    'location_regions': location_regions,
    'neighbors': neighbors,
    'neighborhoods': neighborhoods,
    'map_center': {
        'x': cx,
        'y': cy,
        'r': r
    }
}

with open(filename, 'w') as outfile:
    json.dump(game_config, outfile, indent=4)
