from websockets.asyncio.client import connect
import json
from time import sleep
import uuid
import asyncio
from asyncio import Queue
import os
import discord
from discord import app_commands
from discord.ext import commands, tasks

# All configuration will be defined in the config.json file.

config = json.load(open("config.json", "r"))

client_url = config["ArchipelagoConfig"]["client_url"]
client_port = config["ArchipelagoConfig"]["client_port"]

messages_to_send = Queue() # Queue of messages to send to the server, received from the discord bot

data_dir = "./data"
if not os.path.exists(data_dir) :
    os.makedirs(data_dir)
datapackage_path = f"{data_dir}/datapackage.json"
reversed_datapackage_path = f"{data_dir}/reversed_datapackage.json"
    
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
        self.datapackage = None
        
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
                        self.datapackage = message
                    if message["cmd"] == "Connected" :
                        for slot, slot_info in message["slot_info"].items() :
                            player_slot = slot
                            player_game = slot_info["game"]
                            player_name = slot_info["name"]
                            if player_game == "Archipelago" :
                                continue
                            print(f"Creating player {player_name} in slot {player_slot} playing {player_game}.")
                            await self.player_db.create_player(player_slot, player_game, player_name)
                        # Reverse datapack now (otherwise games is an empty list)
                        await self.build_reverse_data_dict()
                        with open(reversed_datapackage_path, "w", encoding="utf-8") as file:
                            json.dump(self.datapackage, file, indent=2, ensure_ascii=False)
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
            msg_str = ""; flag = None
            msg_summary = []; player_recieving = None
            for data in message["data"] :
                if data["text"] in ["(", ")"] :
                    continue
                elif "type" not in data.keys():
                    msg_str += data["text"]
                elif data["type"] == "player_id" :
                    player_slot = data["text"]
                    player = await self.player_db.get_player(player_slot)
                    msg_str += f"{player.player_name}"
                    msg_summary.append(f"{player.player_name}")
                elif data["type"] == "item_id" :
                    item_id = data["text"]
                    player_recieving = await self.player_db.get_player(data["player"])
                    game_receiving = player_recieving.player_game
                    flag = data["flags"]
                    color = await get_ansi_color_from_flag(flag)
                    # find item name in datapackage
                    item_name = self.datapackage["data"]["games"][game_receiving]["id_to_item_name"][item_id]
                    msg_str += f"\u001b[0;{color}m{item_name}\u001b[0m"
                    msg_summary.append(item_name)
                elif data["type"] == "location_id" :
                    location_id = data["text"]
                    player_sending = await self.player_db.get_player(data["player"])
                    game_sending = player_sending.player_game
                    location_name = self.datapackage["data"]["games"][game_sending]["id_to_location_name"][location_id]
                    msg_str += f"\nCheck: {location_name}"
                    msg_summary.append(location_name)
                else :
                    print(f"Unknown data type : {data["type"]}")
            if player_recieving is None :
                raise ValueError(f"Player receiving item not found in message : {message}")
            player_recieving.new_items.append((msg_summary, flag))
            await messages_to_send.put((msg_str, flag))

    async def check_data_package(self) -> None :
        print("-- Checking DataPackage.")
        if os.path.exists(datapackage_path) :
            self.datapackage = json.load(open(datapackage_path, "r"))
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
        played_games = await self.player_db.get_all_played_games()
        print(f"Keeping games : {played_games}")
        for game_name, game_data in games.items():
            if game_name not in played_games :
                continue # No need to store data for unplayed games
            reverse["data"]["games"][game_name] = {
                "id_to_item_name": {},
                "id_to_location_name": {}
            }
            for item_name, item_id in game_data["item_name_to_id"].items():
                reverse["data"]["games"][game_name]["id_to_item_name"][item_id] = item_name
            for location_name, location_id in game_data["location_name_to_id"].items() :
                reverse["data"]["games"][game_name]["id_to_location_name"][location_id] = location_name
        self.datapackage = reverse

async def get_ansi_color_from_flag(flag: int) -> int :
    if flag & 0b001 :
        return 33 # ANSI code for yellow
    elif flag & 0b010 :
        return 34 # ANSI code for blue
    elif flag & 0b100 :
        return 31 # ANSI code for red
    else :
        return 37 # ANSI code for white

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
        self.new_items = [] # List of new items received, to be sent to discord when queried

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

    async def get_player_by_slot(self, player_slot : int) -> Player :
        return self.players.get(player_slot, None)
    
    async def get_player_by_name(self, player_name : str) -> Player :
        for player in self.players.values() :
            if player.player_name == player_name :
                return player
        return None

    async def get_player_by_discord_id(self, discord_id : int) -> Player :
        for player in self.players.values() :
            if player.discord_id == discord_id :
                return player
        return None
    
    async def get_all_players_names(self) -> list[str] :
        return [player.player_name for player in self.players.values()]
    
    async def get_all_played_games(self) -> list[str] :
        return [player.player_game for player in self.players.values()]
    
    async def get_all_discord_ids(self) -> list[int] :
        return [player.discord_id for player in self.players.values() if player.discord_id is not None]

# Init player db and tracker :
tracker_client = TrackerClient()


# ==============================================================
#                     Discord Bot part
# ==============================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
NORMAL_CHANNEL_ID = config["DiscordConfig"]["normal_channel_id"]
ADMIN_CHANNEL_ID = config["DiscordConfig"]["admin_channel_id"]
APP_TOKEN = config["DiscordConfig"]["app_token"]

@bot.command()
async def players(ctx):
    players = await tracker_client.player_db.get_all_players_names()
    await ctx.send("test")

@bot.command()
async def register(ctx, player_name: str) :
    # Check if player name is valid
    if player_name not in await tracker_client.player_db.get_all_players_names() :
        await ctx.send(f"Player name {player_name} not found. Please check the spelling and try again.\n\
Available player names are : {', '.join(await tracker_client.player_db.get_all_players_names())}")
    elif await tracker_client.player_db.get_player_by_name(player_name) is not None :
        player = await tracker_client.player_db.get_player_by_name(player_name)
        await ctx.send(f"Player {player_name} is already registered by {player.discord_id}.\nIf you think this is an error, please contact the administrator.")
    else :
        # Get discord id of the user
        discord_id = ctx.author.id
        player = await tracker_client.player_db.get_player_by_name(player_name)
        player.discord_id = discord_id
        await ctx.send(f"Player {player_name} successfully registered to discord user {ctx.author.name}#{ctx.author.discriminator}.")

@bot.command()
async def unregister(ctx, player_name: str) :
    # Check if player name is valid
    if player_name not in await tracker_client.player_db.get_all_players_names() :
        await ctx.send(f"Player name {player_name} not found. Please check the spelling and try again.\n\
Available player names are : {', '.join(await tracker_client.player_db.get_all_players_names())}")
    else :
        player = await tracker_client.player_db.get_player_by_name(player_name)
        if player.discord_id is None :
            await ctx.send(f"Player {player_name} is not registered to any discord user.")
        elif player.discord_id != ctx.author.id :
            await ctx.send(f"Player {player_name} is registered to another discord user. You cannot unregister it.\nIf you think this is an error, please contact the administrator.")
        else :
            player.discord_id = None
            await ctx.send(f"Player {player_name} successfully unregistered from discord user {ctx.author.name}#{ctx.author.discriminator}.")

@tasks.loop(seconds=1)
async def process_new_items() :
    while not messages_to_send.empty() :
        msg_str = await messages_to_send.get()
   

@bot.command()
async def test(ctx) :
    message = "```ansi\n\u001b[0;33mYellow item\u001b[0m \n\u001b[0;34mBlue item\u001b[0m \n\u001b[0;31mRed item\u001b[0m \nNormal text```"
    await ctx.send(message)

async def main():

    await asyncio.gather(
        tracker_client.run(),
        bot.start(APP_TOKEN)
    )

if __name__ == "__main__":
    asyncio.run(main())