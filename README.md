# arrakis

Generating a debugging map of Arrakis that displays neighborhood graph and regions.

```python
from arrakis.generator import generateNeighborhood
from arrakis.poly import extract, getRegionsLocations, findIntersections, findNeighboring, findCenters

areas = extract()

regions, locations = getRegionsLocations(areas)

location_regions = findIntersections(areas, regions, locations)

neighbors = findNeighboring(areas, regions, locations, skip=['arrakis', 'tleilaxu_tanks'])

centers = findCenters(areas, locations)

outfile = 'images/cartography.jpg'
generateNeighborhood(centers, locations, neighbors, location_regions, outfile, quality=95, skip=['arrakis'])
```

renders

![arrakis_cartography](https://github.com/marekyggdrasil/arrakis/master/images/cartography.jpg)

## Credits

Game assets from [Sorvan's website](http://www.sorvan.com/games/dune/).

For vectorizing regions on the map we used the [summerstyle editor](https://summerstyle.github.io/summer/#).
