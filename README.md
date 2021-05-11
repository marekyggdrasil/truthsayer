# arrakis

You can generate a map of Arrakis as follows

```python
from arrakis.generator import generate

factions = [
    'atreides_paul_muaddib.png',
    'bene_gesserit_mother_mohian.png',
    'harkonnen_baron_harkonnen.png',
    'emperor_emperor_shaddam_iv.png',
    'fremen_liet_kynes.png',
    'guild_edric.png']
tanks = []
territories = {}
texts = {
    'promo_top': 'Truthsayer Discord',
    'promo': 'Join us for more Dune games!',
    'game_info': 'Game #21762\nTurn 6\nMentat phase',
    'qr': 'https://discord.gg/VVYM22Hs2t',
    'usernames': [
        '@username\nHouse Atreides',
        '@username\nBene Gesserit',
        '@username\nHouse Harkonnen',
        '@username\nEmperor',
        '@username\nFremen',
        '@username\nSpacing Guild']
}
outfile = 'images/arrakis.jpg'
generate(factions, tanks, territories, texts, outfile)
```

renders

![arrakis_cartography](https://github.com/marekyggdrasil/arrakis/blob/main/images/arrakis.jpg?raw=true)

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

![arrakis_cartography](https://github.com/marekyggdrasil/arrakis/blob/main/images/cartography.jpg?raw=true)

## Credits

Game assets from [Sorvan's website](http://www.sorvan.com/games/dune/).

For vectorizing regions on the map we used the [summerstyle editor](https://summerstyle.github.io/summer/#).

For creating transparency on the battle wheels used [online png tools](https://onlinepngtools.com/create-transparent-png).
