from models.item import Item

PLAYER_COLORS = [
    "\u001b[30m",
    "\u001b[31m",
    "\u001b[32m",
    "\u001b[33m",
    "\u001b[34m",
    "\u001b[35m",
    "\u001b[36m",
]


class Player:
    def __init__(self, player_slot, player_game, player_name, discord_id=None):
        self.player_slot = player_slot
        self.player_game = player_game
        self.player_name = player_name
        self.discord_id = discord_id
        self.new_items = []
        self.todolist = []
        self.allow_ping = True
        self.color = PLAYER_COLORS[int(player_slot) % len(PLAYER_COLORS)]
        self.name_colored = f"{self.color}{self.player_name}\u001b[0m"
        self.is_playing = False
        self.time_joined = 0.0
        self.time_played = 0.0 # seconds

    def save(self):
        return {
            "player_slot": self.player_slot,
            "player_game": self.player_game,
            "player_name": self.player_name,
            "discord_id": self.discord_id,
            "new_items": [item.save() for item in self.new_items],
            "todolist": [item.save() for item in self.todolist],
            "allow_ping": self.allow_ping,
            "time_played": self.time_played
        }
    
    def load(self, data : dict) -> 'Player' :
        player = Player(
            player_slot=data["player_slot"],
            player_game=data["player_game"],
            player_name=data["player_name"],
            discord_id=data["discord_id"]
        )
        player.color = PLAYER_COLORS[int(player.player_slot) % len(PLAYER_COLORS)]
        player.name_colored = f"{player.color}{player.player_name}\u001b[0m"
        player.new_items = [Item.load(item_data) for item_data in data.get("new_items", [])]
        player.todolist = [Item.load(item_data) for item_data in data.get("todolist", [])]
        player.allow_ping = data.get("allow_ping", True)
        player.time_played = data.get("time_played", 0.0)
        player.is_playing = False
        player.time_joined = 0.0
        return player