from arrakis.poly import extract, getRegionsLocations, findNeighboring, findIntersections, findStorm


areas = extract()
regions, locations = getRegionsLocations(areas)
location_regions = findIntersections(areas, regions, locations)
neighbors = findNeighboring(areas, regions, locations, skip=['arrakis', 'tleilaxu_tanks'])

cx, cy, r = findStorm(areas)
print(cx, cy, r)
