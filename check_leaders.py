from truthsayer.processor import ConfigManager

manager = ConfigManager()
for faction in manager.getFactions():
    leaders = manager.getLeaders(faction)
    print(faction)
    print(leaders)
    print()
    leaders_choices = manager.getLeadersChoices(faction)
    print(leaders_choices)
    print()
