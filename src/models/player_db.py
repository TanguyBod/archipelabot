import json
import os
import aiofiles
from models.player import Player

class PlayerDB :
    def __init__(self, file_path: str = None) :
        self.file_path = file_path
        self.players_by_slot: dict[int, Player] = {}
        self.players_by_name: dict[str, Player] = {}
        self.players_by_discord: dict[int, Player] = {}
        if file_path is not None and os.path.exists(file_path) :
            self.load_db(file_path)
            print(f"PlayerDB initialized with {len(self.players_by_name)} players from {file_path}.")
        else :  
            print("PlayerDB initialized empty.")

    def create_player(self, 
                      player_slot : int, 
                      player_game : str, 
                      player_name : str, 
                      discord_id : int = None
                    ) -> Player :
        if player_slot in self.players_by_slot:
            raise ValueError(f"Player slot {player_slot} already exists.")
        player = Player(int(player_slot), player_game, player_name, discord_id)
        self.players_by_slot[player_slot] = player
        self.players_by_name[player_name] = player
        if discord_id is not None:
            self.players_by_discord[discord_id] = player
        return player

    def get_player_by_slot(self, player_slot : int) -> Player :
        return self.players_by_slot.get(player_slot)

    def get_player_by_name(self, player_name : str) -> Player :
        return self.players_by_name.get(player_name)

    def get_player_by_discord_id(self, discord_id : int) -> Player :
        return self.players_by_discord.get(discord_id)

    def get_all_players_names(self) -> list[str] :
        return [player.player_name for player in self.players_by_name.values()]
    
    def get_all_played_games(self) -> list[str] :
        return [player.player_game for player in self.players_by_name.values()]
    
    def get_all_discord_ids(self) -> list[int] :
        return [player.discord_id for player in self.players_by_discord.values() if player.discord_id is not None]

    def print_players(self) -> None :
        for player in self.players_by_name.values() :
            print(f"Player {player.player_name or 'Unknown'} in slot {player.player_slot or 'Unknown'} playing {player.player_game or 'Unknown'} registered to discord id {player.discord_id or 'Unknown'}.")

    def set_discord_id(self, player, discord_id):
        if player.discord_id:
            self.players_by_discord.pop(player.discord_id, None)
        player.discord_id = discord_id
        self.players_by_discord[discord_id] = player

    def save_db(self, file_path: str) -> None :
        with open(file_path, "w") as f:
            json.dump({player_name: player.save() for player_name, player in self.players_by_name.items()}, f, indent=4)

    def load_db(self, file_path: str) -> None :
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
                for player_name, player_data in data.items():
                    player = Player.load(player_data)
                    self.players_by_slot[player.player_slot] = player
                    self.players_by_name[player.player_name] = player
                    if player.discord_id is not None:
                        self.players_by_discord[player.discord_id] = player
        except FileNotFoundError:
            print(f"No existing database found at {file_path}. Starting with an empty database.")