from archipelago.base_client import ArchipelagoClient
from models.player_db import PlayerDB
from models.item import Item
from utils.colors import get_ansi_color_from_flag
from discord_bot.texts_flavors import get_fulfilled_wish_flavor, get_deathlink_flavor
import time
import logging
import asyncio
import aiofiles
import json
import os


class BotClient(ArchipelagoClient) :
    def __init__(self, config: dict[str, any], message_queue: asyncio.Queue, ping_queue: asyncio.Queue, dm_queue: asyncio.Queue, logger: logging.Logger) :
        super().__init__(config, logger=logger)
        # Make sure data directory exists
        os.makedirs(config["DatabaseConfig"]["data_directory"], exist_ok=True)
        self.tags = set({'TextOnly', 'Tracker', 'DeathLink'})
        self.slot_name : str = config["ArchipelagoConfig"]["bot_slot"]
        self.ap_connection = None
        self.player_db = PlayerDB(config["DatabaseConfig"]["data_directory"]+"/players.json")
        self.datapackage = None
        self.datapackage_reversed = False 
        self.lock = asyncio.Lock() # Lock to protect shared resources
        self.workers_started = False
        self.messages_to_send = message_queue
        self.ping_queue = ping_queue
        self.dm_queue = dm_queue
        self.datapackage_path = os.path.join(config["DatabaseConfig"]["data_directory"], "datapackage.json")
        self.reversed_datapackage_path = os.path.join(config["DatabaseConfig"]["data_directory"], "reversed_datapackage.json")
        self.custom_deathlink_flavor = config["AdvancedConfig"].get("custom_deathlink_flavor", False)
    
    async def process_messages(self):
        while self.running:
            try :
                message = await self.message_queue.get()
                self.logger.info(f"Processing message: {message}")
                if message["cmd"] == "RoomInfo" :
                    # Check DataPackage and send connect
                    await self.check_data_package()
                    await self.send_connect()
                elif message["cmd"] == "DataPackage" :
                    # save DataPackage in a json, needed if bot is restarted
                    async with aiofiles.open(self.datapackage_path, "w", encoding="utf-8") as file:
                        await file.write(json.dumps(message, indent=2, ensure_ascii=False))
                    self.datapackage = message
                    await self.build_reverse_data_dict()
                    async with aiofiles.open(self.reversed_datapackage_path, "w", encoding="utf-8") as file:
                        await file.write(json.dumps(self.datapackage, indent=2, ensure_ascii=False))
                    self.datapackage_reversed = True
                elif message["cmd"] == "Connected" :
                    if self.player_db.loaded_from_file :
                        self.logger.info("PlayerDB loaded from file, skipping player creation from RoomInfo message.")
                    else :
                        for slot, slot_info in message["slot_info"].items() :
                            player_slot = int(slot)
                            player_game = slot_info["game"]
                            player_name = slot_info["name"]
                            if player_game == "Archipelago" :
                                continue
                            self.logger.info(f"Creating player {player_name} in slot {player_slot} playing {player_game}.")
                            self.player_db.create_player(player_slot, player_game, player_name)
                elif message["cmd"] == "PrintJSON" :
                    await self.process_json_message(message)
                elif message["cmd"] == "Bounced" :
                    await self.process_bounced_message(message)
            except Exception as e :
                self.logger.error(f"Error processing message: {e} -->\n {message}")
                continue

    async def process_bounced_message(self, message: dict) -> None :
        if message["tags"] == ['DeathLink'] :
            self.logger.info(f"Processing DeathLink message")
            dead_player_name = message["data"]['source']
            death_time = message["data"]['time']
            death_cause = message["data"]['cause']
            if self.custom_deathlink_flavor :
                msg = get_deathlink_flavor(dead_player_name, death_time)
            else :
                time_struct = time.localtime(death_time)
                time_str = time.strftime("%m-%d %H:%M:%S", time_struct)
                msg = f"```ansi\n💀 \u001b[0;31m[{time_str}]\u001b[0m {dead_player_name} : {death_cause}\n```"
            self.logger.info(f"DeathLink : {dead_player_name} died at {death_time} with cause : {death_cause}")
            await self.messages_to_send.put(msg)
            player = self.player_db.get_player_by_name(dead_player_name)
            if player is not None :
                player.deaths.append(player.time_played + time.time() - player.time_joined) # Add current session time to total time played for accurate death time
                self.logger.info(f"Player {player.player_name} now has {len(player.deaths)} deaths.")
            else :
                self.logger.warning(f"Player {dead_player_name} not found in player_db, cannot update deaths.")

    async def process_json_message(self, message: dict) -> None :
        if message["type"] == "Chat" :
            data_list = message["data"]
            for data in data_list :
                if "!hint" in data["text"] :
                    continue
                await self.messages_to_send.put(data['text'])
        elif message["type"] == "ItemSend" :
            msg_str = ""
            for data in message["data"] :
                if data["text"].strip() in ["(", ")"] :
                    continue
                elif "type" not in data.keys():
                    msg_str += data["text"]
                elif data["type"] == "player_id" :
                    player_slot = int(data["text"])
                    player = self.player_db.get_player_by_slot(player_slot)
                    msg_str += f"{player.name_colored}"
                elif data["type"] == "item_id" :
                    item_id = data["text"]
                    player = self.player_db.get_player_by_slot(int(data["player"]))
                    game = player.player_game
                    flag = data["flags"]
                    color = await get_ansi_color_from_flag(flag)
                    item_name = self.datapackage["data"]["games"][game]["id_to_item_name"][item_id]
                    msg_str += f"\u001b[0;{color}m{item_name}\u001b[0m"
                elif data["type"] == "location_id" :
                    location_id = data["text"]
                    player = self.player_db.get_player_by_slot(int(data["player"]))
                    game = player.player_game
                    location_name = self.datapackage["data"]["games"][game]["id_to_location_name"][location_id]
                    msg_str += f"\nCheck: {location_name}"
                else :
                    self.logger.warning(f"Unknown data type : {data['type']}")
            msg_str = "```ansi\n"+ msg_str +"\n```"
            
            # Now create the item :
            item_sent = await self.process_item_send(receiving_field = message["receiving"], item_field = message["item"])
            if not item_sent :
                self.logger.warning(f"Failed to process item send message, missing field : {message}")
                return
            # Add item to recieving player's new items list if the item is sent from another player and the recieving player is not playing
            # We assume that if the player is playing, they are aware of the items they received
            if item_sent.player_sending != item_sent.player_recieving and not item_sent.player_recieving.is_playing :
                self.logger.info(f"Item sent from {item_sent.player_sending.player_name} added to player {item_sent.player_recieving.player_name} new items list.")
                async with self.lock:
                    item_sent.player_recieving.new_items.append(item_sent)
            item_sent.player_sending.checked_locations += 1 # Keep track of number of checks locations
            await self.remove_item_from_todolist(item_sent)
            await self.messages_to_send.put(msg_str)
            
        elif message["type"] == "Join" :
            if message["tags"] == ["TextOnly"] :
                self.logger.info(f"Received Join message from TextOnly client, ignoring it for player count : {message['slot']}")
                return # Ignore Join messages from TextOnly clients, count only when playing
            player_slot = int(message["slot"])
            player = self.player_db.get_player_by_slot(player_slot)
            if player is None :
                self.logger.warning(f"Player in slot {player_slot} not found in player_db, cannot process Join message.")
                return
            player.is_playing = True
            player.time_joined = time.time()
            self.logger.info(f"Player {player.player_name} in slot {player_slot} started playing, timer started.")
            # If player has new items and get_new_items_auto is enabled, send a message to ping the player about their new items
            if player.new_items and player.get_new_items_auto :
                await self.dm_queue.put((player, "new_items"))
            
        elif message["type"] == "Part" :
            if "['TextOnly']" in message["data"][0]["text"] :
                self.logger.info(f"Received Part message from TextOnly client, ignoring it for player count : {message['slot']}")
                return # Ignore Part messages from TextOnly clients, count only when playing
            player_slot = int(message["slot"])
            player = self.player_db.get_player_by_slot(player_slot)
            if player is None :
                self.logger.warning(f"Player in slot {player_slot} not found in player_db, cannot process Part message.")
                return
            if player.is_playing :
                player.is_playing = False
                time_played = time.time() - player.time_joined
                player.time_played += time_played
                self.logger.info(f"Player {player.player_name} in slot {player_slot} played for {time_played:.2f} seconds, total time played : {player.time_played:.2f} seconds.")
            else :
                self.logger.warning(f"Received Part message for player {player.player_name} in slot {player_slot} but player was not marked as playing.")
        else :
            self.logger.warning(f"Unknown message type : {message['type']} --> \n {message}")

    async def process_item_send(self, receiving_field: str, item_field: dict) -> Item :
        player_recieving = self.player_db.get_player_by_slot(int(receiving_field))
        player_sending = self.player_db.get_player_by_slot(int(item_field["player"]))
        item_id = item_field["item"]
        location_id = item_field["location"]
        flag = item_field["flags"]
        game_receiving = player_recieving.player_game
        game_sending = player_sending.player_game
        item_name = self.datapackage["data"]["games"][game_receiving]["id_to_item_name"][str(item_id)]
        location_name = self.datapackage["data"]["games"][game_sending]["id_to_location_name"][str(location_id)]
        # if one of the fields is missing, log a warning and return None
        if None in [player_recieving, player_sending, item_id, location_id, item_name, location_name] :
            self.logger.warning(f"Missing field in item send message : {receiving_field} {item_field}")
            return None
        item = Item(
            item_name = item_name,
            item_id = item_id,
            location_name = location_name,
            location_id = location_id,
            player_sending = player_sending,
            player_recieving = player_recieving,
            flag = flag
        )
        return item 

    async def remove_item_from_todolist(self, item: Item) -> bool :
        player_sending = self.player_db.get_player_by_name(item.player_sending.player_name)
        for item_todo in player_sending.todolist :
            if item.item_name == item_todo.item_name and item.location_name == item_todo.location_name :
                self.logger.info(f"Item {item.item_name} found in {item.player_sending.player_name} todolist, removing it.")
                player_sending.todolist.remove(item_todo)
                sending_str = item.player_sending.player_name
                recieving_str = f"<@{item.player_recieving.discord_id}>" if item.player_recieving.allow_ping and item.player_recieving.discord_id is not None else item.player_recieving.player_name
                msg_flavor = get_fulfilled_wish_flavor(sending_str, recieving_str, item.item_name, item.location_name)
                await self.ping_queue.put(msg_flavor)
                return True
        self.logger.info(f"Item {item.item_name} not found in {item.player_sending.player_name} todolist, not removed.")
        return False

    async def check_data_package(self) -> None :
        self.logger.info("-- Checking DataPackage.")
        if os.path.exists(self.reversed_datapackage_path) :
            self.datapackage_reversed = True
            async with aiofiles.open(self.reversed_datapackage_path, "r") as f:
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
        self.logger.info("-- Building reverse datapackage.")
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
