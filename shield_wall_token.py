import json

from truthsayer.poly import extract

from shapely.geometry import Polygon

areas = extract()

shield_wall_points = []
min_x, max_x, min_y, max_y = 2**20, 0, 2**20, 0
for x, y in areas['polygons']['shield_wall']:
    shield_wall_points.append((x, -y))
    if x < min_x:
        min_x = x
    if y < min_y:
        min_y = y
    if x > max_x:
        max_x = x
    if y > max_y:
        max_y = y

len_x = max_x - min_x
len_y = max_y - min_y

print('min_x', min_x)
print('max_x', max_x)
print('min_y', min_y)
print('max_y', max_y)
print('')
print('len_x', len_x)
print('len_y', len_y)

shield_wall = Polygon(shield_wall_points)

with open('shield_wall_shape.svg', 'w') as f:
    f.write(shield_wall._repr_svg_())

filename = 'truthsayer/assets/game_config.json'
game_config = None
with open(filename) as json_file:
    game_config = json.load(json_file)

game_config['generated']['shield_wall_token'] = {
    'min_x': min_x,
    'max_x': max_x,
    'min_y': min_y,
    'max_y': max_y,
    'len_x': len_x,
    'len_y': len_y
}

with open(filename, 'w') as outfile:
    json.dump(game_config, outfile)

# convert shield_wall_shape.png -trim shield_wall_shape_trimmed.png
# convert shield_wall_shape_trimmed.png -resize '288x244^' -gravity center shield_wall_destroyed.png
