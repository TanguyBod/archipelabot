from archipelago.base_client import ArchipelagoClient
from models.player_db import PlayerDB
from models.item import Item
from utils.colors import get_ansi_color_from_flag
import asyncio
import aiofiles
import json
import os


class TrackerClient(ArchipelagoClient) :
    def __init__(self, config: dict[str, any], message_queue: asyncio.Queue) :
        super().__init__(config)
        self.tags = set({'TextOnly', 'Tracker', 'DeathLink'})
        self.slot_name : str = config["ArchipelagoConfig"]["bot_slot"]
        self.ap_connection = None
        self.player_db = PlayerDB()
        self.datapackage = None
        self.lock = asyncio.Lock() # Lock to protect shared resources
        self.workers_started = False
        self.messages_to_send = message_queue
        self.datapackage_path = os.path.join(config["DatabaseConfig"]["data_directory"], "datapackage.json")
        self.reversed_datapackage_path = os.path.join(config["DatabaseConfig"]["data_directory"], "reversed_datapackage.json")
    
    async def process_messages(self):
        while self.running:
            try :
                message = await self.message_queue.get()
                print(message)
                if message["cmd"] == "RoomInfo" :
                    # Check DataPackage and send connect
                    await self.check_data_package()
                    await self.send_connect()
                if message["cmd"] == "DataPackage" :
                    # save DataPackage in a json, needed if bot is restarted
                    async with aiofiles.open(self.datapackage_path, "w", encoding="utf-8") as file:
                        await file.write(json.dumps(message, indent=2, ensure_ascii=False))
                    self.datapackage = message
                if message["cmd"] == "Connected" :
                    for slot, slot_info in message["slot_info"].items() :
                        player_slot = int(slot)
                        player_game = slot_info["game"]
                        player_name = slot_info["name"]
                        if player_game == "Archipelago" :
                            continue
                        print(f"Creating player {player_name} in slot {player_slot} playing {player_game}.")
                        self.player_db.create_player(player_slot, player_game, player_name)
                    # Reverse datapack now (otherwise games is an empty list)
                    await self.build_reverse_data_dict()
                    async with aiofiles.open(self.reversed_datapackage_path, "w", encoding="utf-8") as file:
                        await file.write(json.dumps(self.datapackage, indent=2, ensure_ascii=False))
                if message["cmd"] == "PrintJSON" :
                    await self.process_json_message(message)
            except Exception as e :
                print(f"Error processing message: {e}")
                continue

    async def process_json_message(self, message: dict) -> None :
        if message["type"] == "Chat" :
            data_list = message["data"]
            for data in data_list :
                if "!hint" in data["text"] :
                    continue
                await self.messages_to_send.put(data['text'])
        if message["type"] == "ItemSend" :
            msg_str = ""; flag = None; item_player = Item()
            msg_summary = []; player_recieving = None; player_sending = None
            for data in message["data"] :
                if data["text"].strip() in ["(", ")"] :
                    continue
                elif "type" not in data.keys():
                    msg_str += data["text"]
                elif data["type"] == "player_id" :
                    player_slot = int(data["text"])
                    player_sending = self.player_db.get_player_by_slot(player_slot)
                    msg_str += f"{player_sending.player_name}"
                    msg_summary.append(f"{player_sending.player_name}")
                    item_player.player_sending = player_sending
                elif data["type"] == "item_id" :
                    item_id = data["text"]
                    player_recieving = self.player_db.get_player_by_slot(int(data["player"]))
                    game_receiving = player_recieving.player_game
                    flag = data["flags"]
                    color = await get_ansi_color_from_flag(flag)
                    item_name = self.datapackage["data"]["games"][game_receiving]["id_to_item_name"][item_id]
                    msg_str += f"\u001b[0;{color}m{item_name}\u001b[0m"
                    msg_summary.append(item_name)
                    item_player.item_name = item_name
                    item_player.item_id = item_id
                    item_player.game = game_receiving
                    item_player.flag = flag
                elif data["type"] == "location_id" :
                    location_id = data["text"]
                    player_sending = self.player_db.get_player_by_slot(int(data["player"]))
                    game_sending = player_sending.player_game
                    location_name = self.datapackage["data"]["games"][game_sending]["id_to_location_name"][location_id]
                    msg_str += f"\nCheck: {location_name}"
                    msg_summary.append(location_name)
                    item_player.location_name = location_name
                    item_player.location_id = location_id
                else :
                    print(f"Unknown data type : {data['type']}")
            if player_recieving is None :
                raise ValueError(f"Player receiving item not found in message : {message}")
            if player_sending.player_slot != player_recieving.player_slot :
                print(f"Item sent from {player_sending.player_name} added to player {player_recieving.player_name} new items list.")
                async with self.lock:
                    player_recieving.new_items.append(item_player)
            msg_str = "```ansi\n"+ msg_str +"\n```"
            await self.messages_to_send.put(msg_str)
        else :
            print(f"Unknown message type : {message['type']}")

    async def check_data_package(self) -> None :
        print("-- Checking DataPackage.")
        if os.path.exists(self.datapackage_path) :
            async with aiofiles.open(self.datapackage_path, "r") as f:
                self.datapackage = json.loads(await f.read())
            return
        payload = {
            'cmd': 'GetDataPackage'
        }
        await self.send_message(payload)
            
    async def build_reverse_data_dict(self):
        """
        Build a reverse data dict to allow efficient data retrieval.
        Reverse item_name_to_id and location_name_to_id to id_to_item_name
        and id_to_location_name.
        """
        
        if self.datapackage is None :
            raise ValueError(f"Trying to reverse datapackage but it is empty")
        reverse = {"cmd": "DataPackage", "data" : {"games" : {}}}
        games = self.datapackage["data"]["games"]
        played_games = self.player_db.get_all_played_games()
        for game_name, game_data in games.items():
            if game_name not in played_games :
                continue # No need to store data for unplayed games
            reverse["data"]["games"][game_name] = {
                "id_to_item_name": {},
                "id_to_location_name": {}
            }
            for item_name, item_id in game_data["item_name_to_id"].items():
                reverse["data"]["games"][game_name]["id_to_item_name"][str(item_id)] = item_name
            for location_name, location_id in game_data["location_name_to_id"].items() :
                reverse["data"]["games"][game_name]["id_to_location_name"][str(location_id)] = location_name
        self.datapackage = reverse