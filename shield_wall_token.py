from truthsayer.poly import extract

from shapely.geometry import Polygon

areas = extract()

shield_wall_points = []
for x, y in areas['polygons']['shield_wall']:
    shield_wall_points.append((x, -y))

shield_wall = Polygon(shield_wall_points)

with open('shield_wall_shape.svg', 'w') as f:
    f.write(shield_wall._repr_svg_())
