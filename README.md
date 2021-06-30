# arrakis

You can generate a map of Arrakis as follows

```python
from truthsayer.processor import Caretaker, OriginatorTruthsayer

meta = {
    'factions': {},
    'usernames': {},
    'user_ids': {},
    'texts': {
        'promo_top': 'Truthsayer Discord',
        'promo': 'Join us for more Dune games!',
        'game_id': '#21762',
        'game_turn': 6,
        'game_phase': 'Battle',
        'qr': 'https://discord.gg/VVYM22Hs2t',
        'commands': []
    }
}

originator = OriginatorTruthsayer(meta=meta)
caretaker = Caretaker(originator)

originator.render('images/originator/originator00.jpg')

originator.join(1, '@marek', '#467263')
caretaker.backup()

originator.join(5, '@renzokuken', '#387843')
caretaker.backup()

originator.join(3, '@zylwia', '#198264')
caretaker.backup()

originator.render('images/originator/originator01.jpg')

originator.join(2, '@andy', '#430293')
caretaker.backup()

originator.join(4, '@john', '#098532')
caretaker.backup()

originator.join(6, '@somedude', '#130539')
caretaker.backup()

originator.render('images/originator/originator02.jpg')

originator.randomize('factions')
caretaker.backup()

originator.render('images/originator/originator03.jpg')

originator.initgame()
caretaker.backup()

originator.render('images/originator/originator04.jpg')

originator.ship('emperor', 'plastic_basin', 'R13', 4)
caretaker.backup()

originator.render('images/originator/originator05.jpg')

originator.move('atreides', 'arrakeen', 'R10', 'hole_in_the_rock', 'R9', 3)
caretaker.backup()

originator.render('images/originator/originator06.jpg')
```

![arrakis_cartography](https://github.com/marekyggdrasil/arrakis/blob/main/images/originator/originator06.jpg?raw=true)

We can move the storm, undo moves, cause Spiceblow and change sprite assets

```python
originator.storm('R9')
caretaker.backup()

originator.render('images/originator/originator07.jpg')

originator.spiceblow('sihaya_ridge', 5)
caretaker.backup()

originator.render('images/originator/originator08.jpg')

# try to undo the move
caretaker.undo()

originator.render('images/originator/originator09.jpg')

originator.config('spice_token', 'spiceglow', 500)
caretaker.backup()

originator.render('images/originator/originator10.jpg')
```

![arrakis_cartography](https://github.com/marekyggdrasil/arrakis/blob/main/images/originator10.jpg?raw=true)

Now few examples how to draw cards and conduct the battle phase

```python
# draw some cards
originator.draw('player_1', 'treachery')
caretaker.backup()

originator.draw('player_1', 'treachery')
caretaker.backup()

originator.draw('player_2', 'treachery')
caretaker.backup()

originator.draw('player_2', 'treachery')
caretaker.backup()

# initiate battle
hand_player_1 = originator.hand('player_1')
hand_player_2 = originator.hand('player_2')

print('player_1 hand')
print(hand_player_1)

print('player_2 hand')
print(hand_player_2)

originator.battle('player_1', 'player_2')
caretaker.backup()

originator.deployment('player_1', 3)
caretaker.backup()

originator.lead('player_1', 'thufir_hawat')
caretaker.backup()

originator.treachery('player_1', hand_player_1['cards'][0])
caretaker.backup()

originator.deployment('player_2', 4)
caretaker.backup()

originator.lead('player_2', 'alia')
caretaker.backup()

originator.treachery('player_2', hand_player_2['cards'][0])
caretaker.backup()

originator.render('images/originator/originator11.jpg', battle=True)
```

![arrakis_cartography](https://github.com/marekyggdrasil/arrakis/blob/main/images/originator/originator11.jpg?raw=true)

## Credits

Game assets from [Sorvan's website](http://www.sorvan.com/games/dune/).

For vectorizing regions on the map we used the [summerstyle editor](https://summerstyle.github.io/summer/#).

For creating transparency on the battle wheels used [online png tools](https://onlinepngtools.com/create-transparent-png).
