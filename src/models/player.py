from models.item import Item

class Player:
    def __init__(self, player_slot, player_game, player_name, discord_id=None):
        self.player_slot = player_slot
        self.player_game = player_game
        self.player_name = player_name
        self.discord_id = discord_id
        self.new_items = []
        self.todolist = []
        self.allow_ping = True

    def save(self):
        return {
            "player_slot": self.player_slot,
            "player_game": self.player_game,
            "player_name": self.player_name,
            "discord_id": self.discord_id,
            "new_items": [item.save() for item in self.new_items],
            "todolist": [item.save() for item in self.todolist],
            "allow_ping": self.allow_ping
        }
    
    def load(data):
        player = Player(
            player_slot=data["player_slot"],
            player_game=data["player_game"],
            player_name=data["player_name"],
            discord_id=data["discord_id"]
        )
        player.new_items = [Item.load(item_data) for item_data in data.get("new_items", [])]
        player.todolist = [Item.load(item_data) for item_data in data.get("todolist", [])]
        player.allow_ping = data.get("allow_ping", True)
        return player