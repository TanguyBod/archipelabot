from models.player import Player

class PlayerDB :
    def __init__(self) :
        self.players_by_slot: dict[int, Player] = {}
        self.players_by_name: dict[str, Player] = {}
        self.players_by_discord: dict[int, Player] = {}

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