from websockets.asyncio.client import connect
import json
from time import sleep
import uuid
import asyncio
from asyncio import Queue
import os

# All configuration will be defined in a config.json file.

config = json.load(open("config.json", "r"))

messages_to_send = Queue() # Queue of messages to send to the server, received from the discord bot

data_dir = "./data"
if not os.path.exists(data_dir) :
    os.makedirs(data_dir)
datapackage_path = f"{data_dir}/datapackage.json"
    
class TrackerClient() :
    tags : set[str] = {'TextOnly', 'Tracker', 'DeathLink'}
    version : dict[str, any] = {"major": 0, "minor": 6, "build": 0, "class": "Version"}
    items_handling: int = 0b000 # Does not receive any items
    
    def __init__(self) :
        self.client_url : str = config["ArchipelagoConfig"]["client_url"]
        self.client_port : str = config["ArchipelagoConfig"]["client_port"]
        self.password : str = config["ArchipelagoConfig"]["password"]
        self.password = self.password if self.password else ""
        self.slot_name : str = config["ArchipelagoConfig"]["bot_slot"]
        self.uuid : int = uuid.getnode()
        self.ap_connection = None
        self.player_db = PlayerDB()
        
    async def connect(self) :
        self.ap_connection = await connect(
            f"ws://{self.client_url}:{self.client_port}",
            max_size=None
        )
    
    async def run(self) :
        await self.connect()
        while True :
            try :
                messages = await self.ap_connection.recv()
                messages = json.loads(messages)
                for message in messages :
                    print(message)
                    # Log message for now :
                    if message["cmd"] == "RoomInfo" :
                        # Check DataPackage and send connect
                        await self.check_data_package()
                        await self.send_connect()
                    if message["cmd"] == "DataPackage" :
                        # save DataPackage in a json, needed if bot is restarted
                        with open(datapackage_path, "w", encoding="utf-8") as file:
                            json.dump(message, file, indent=2, ensure_ascii=False)
                    if message["cmd"] == "Connected" :
                        for slot, slot_info in message["slot_info"].items() :
                            player_slot = slot
                            player_game = slot_info["game"]
                            player_name = slot_info["name"]
                            if player_game == "Archipelago" :
                                continue
                            print(f"Creating player {player_name} in slot {player_slot} playing {player_game}.")
                            await self.player_db.create_player(player_slot, player_game, player_name)
                    if message["cmd"] == "PrintJSON" :
                        await self.process_json_message(message)
            except Exception as e :
                print(f"Error receiving message: {e}")
                break

    async def process_json_message(self, message: dict) -> None :
        if message["type"] == "Chat" :
            data_list = message["data"]
            for data in data_list :
                await messages_to_send.put(data['text'])
        if message["type"] == "Part" :
            

    async def check_data_package(self) -> None :
        print("-- Checking DataPackage.")
        if os.path.exists(datapackage_path) :
            return
        payload = {
            'cmd': 'GetDataPackage'
        }
        await self.send_message(payload)
            
    async def send_connect(self) -> None:
        print("-- Sending `Connect` packet to log in to server.")
        payload = {
            'cmd': 'Connect',
            'game': '',
            'password': self.password,
            'name': self.slot_name,
            'version': self.version,
            'tags': list(self.tags),
            'items_handling': self.items_handling,
            'uuid': self.uuid,
        }
        await self.send_message(payload)
        
    async def send_message(self, message: dict) -> None :
        try :
            await self.ap_connection.send(json.dumps([message]))
        except Exception as e :
            print(f"Error sending message: {e}")

class Player :
    def __init__(self, 
                 player_slot : int,
                 player_game : str,
                 player_name : str,
                 discord_id : int = None
                 ) :
        self.player_slot = player_slot
        self.player_game = player_game
        self.player_name = player_name
        self.discord_id = discord_id
    

class PlayerDB :
    def __init__(self) :
        self.players : dict[int, Player] = {}

    async def create_player(self, 
                      player_slot : int, 
                      player_game : str, 
                      player_name : str, 
                      discord_id : int = None
                    ) -> Player :
        if player_slot in self.players :
            raise ValueError(f"Player slot {player_slot} already exists.")
        player = Player(player_slot, player_game, player_name, discord_id)
        self.players[player_slot] = player
        return player

    async def get_player(self, player_slot : int) -> Player :
        return self.players.get(player_slot, None)

    async def get_player_by_discord_id(self, discord_id : int) -> Player :
        for player in self.players.values() :
            if player.discord_id == discord_id :
                return player
        return None
    
    async def get_all_players_names(self) -> list[str] :
        return [player.player_name for player in self.players.values()]
    
class TMPPrinter :
    def __init__(self) :
        pass
    
    async def run(self) :
        while True :
            message = await messages_to_send.get()
            print(f"Message to send to server: {message}")
            # TODO: send message to server via discord bot
            await asyncio.sleep(0.1)

        
client_url = "141.253.103.79"
client_port = "38281"

async def main():
    tracker_client = TrackerClient()
    tmp_printer = TMPPrinter()

    await asyncio.gather(
        tracker_client.run(),
        tmp_printer.run()
    )

if __name__ == "__main__":
    asyncio.run(main())