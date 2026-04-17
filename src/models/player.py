class Player:
    def __init__(self, player_slot, player_game, player_name, discord_id=None):
        self.player_slot = player_slot
        self.player_game = player_game
        self.player_name = player_name
        self.discord_id = discord_id
        self.new_items = []
        self.todolist = []
        self.allow_ping = True