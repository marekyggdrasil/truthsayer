from truthsayer.processor import OriginatorTruthsayer

meta = {
    'factions': {
        'player_1': 'atreides',
        'player_2': 'bene_gesserit',
        'player_3': 'emperor',
        'player_4': 'spacing_guild',
        'player_5': 'fremen',
        'player_6': 'harkonnen'
    },
    'usernames': {
        'player_1': '@marek',
        'player_2': '@john',
        'player_3': '@renzokuken',
        'player_4': '@somedude',
        'player_5': '@andy',
        'player_6': '@zylwia'
    },
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
originator.render('images/originator/originator.jpg')

originator.ship('emperor', 'plastic_basin', 'R13', 4)
originator.render('images/originator/originator2.jpg')

originator.move('atreides', 'arrakeen', 'R10', 'hole_in_the_rock', 'R9', 3)
originator.render('images/originator/originator3.jpg')

originator.storm('R9')
originator.render('images/originator/originator4.jpg')

originator.spiceblow('sihaya_ridge', 5)
originator.render('images/originator/originator5.jpg')

# draw some cards
originator.draw('player_1', 'treachery')
originator.draw('player_1', 'treachery')

originator.draw('player_2', 'treachery')
originator.draw('player_2', 'treachery')

# initiate battle
hand_player_1 = originator.hand('player_1')
hand_player_2 = originator.hand('player_2')

print('player_1 hand')
print(hand_player_1)

print('player_2 hand')
print(hand_player_2)

originator.battle('player_1', 'player_2')

originator.deployment('player_1', 3)
originator.lead('player_1', 'thufir_hawat')
originator.treachery('player_1', hand_player_1['cards'][0])

originator.deployment('player_2', 4)
originator.lead('player_2', 'alia')
originator.treachery('player_2', hand_player_2['cards'][0])

originator.render('images/originator/originator6.jpg', battle=True)

