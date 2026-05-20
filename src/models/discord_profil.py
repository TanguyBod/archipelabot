from models.player_db import PlayerDB
import json
import os

class DiscordProfile :
    def __init__(self, name: str, id: int) -> None:
        self.id = id
        self.name = name
        self.slots = []
        self.current_slot = None
        
    def save(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "slots": [slot.player_slot for slot in self.slots],
            "current_slot": self.current_slot.player_slot if self.current_slot else None
        }

    def __str__(self) -> str:
        return str(self.id)
    
class DiscordDB :
    def __init__(self, file_path: str, player_db: PlayerDB) -> None:
        self.file_path = file_path
        self.player_db = player_db
        self.discord_ids = {} 
        if file_path is not None and os.path.exists(file_path) :
            if self.player_db.loaded_from_file == False :
                print("Warning: DiscordDB file found but PlayerDB is not loaded from file. This behavior should not happen. \
Make sure to have both players.json and discord_profiles.json files. If not, delete the discord_profiles.json file and restart the bot.\
You will need to register again.")
            self.load_db(file_path)
            self.loaded_from_file = True
            print(f"DiscordDB initialized with {len(self.discord_ids)} profiles from {file_path}.")
        else :  
            print("DiscordDB initialized empty.")
            
    def save_db(self, file_path: str) -> None:
        data = {
            "discord_ids": {str(id): profile.save() for id, profile in self.discord_ids.items()}
        }
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
    
    def load_db(self, file_path: str) -> None:
        with open(file_path, 'r') as f:
            data = json.load(f)
        for id_str, profile_data in data.get("discord_ids", {}).items():
            id = int(id_str)
            profile = DiscordProfile(
                name=profile_data["name"],
                id=id
            )
            self.discord_ids[id] = profile
            # Link the discord profile to the player slots
            for slot in profile_data.get("slots", []):
                player = self.player_db.get_player_by_slot(slot)
                if player:
                    profile.slots.append(player)
                    if profile_data.get("current_slot") == slot:
                        profile.current_slot = player
                else:
                    print(f"Warning: Player slot {slot} in Discord profile {id} not found in PlayerDB.")

    def add_discord_id(self, discord_id: int, name: str) -> None:
        self.discord_ids[discord_id] = DiscordProfile(name, discord_id)
        
    def add_discord_profile(self, discord_profile: DiscordProfile) -> None:
        self.discord_ids[discord_profile.id] = discord_profile

    def get_discord_profile(self, discord_id: int) -> DiscordProfile:
        profile = self.discord_ids.get(discord_id)
        if profile:
            return profile
        else :
            return None