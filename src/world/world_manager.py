import asyncio
import os
import json
from archipelago.bot_client import BotClient
from discord_bot import bot
from discord_bot.commands import send_new_items

class WorldManager:
    def __init__(self, discord_bot, logger, datadir="./data"):
        self.worlds = {}  # world_id -> WorldSession
        self.bot = discord_bot
        self.logger = logger
        self.datadir = datadir
        self.loaded = False
                
    async def create_world(self, world_data_dir, config):
        world_id = world_data_dir.split("/")[-1]
        message_queue = asyncio.Queue()
        ping_queue = asyncio.Queue()
        dm_queue = asyncio.Queue()
        world_logger = self.logger.getChild(world_id)
        admin_ids = config["DiscordConfig"].get("admin_ids", [])
        normal_channel_id = int(config["DiscordConfig"]["normal_channel_id"])
        for session in self.worlds.values():
            if session.normal_channel_id == normal_channel_id:
                return "already_exists"
        ping_channel_id = int(config["DiscordConfig"].get("ping_channel_id", normal_channel_id))

        bot_client = BotClient(
            config = config,
            message_queue = message_queue,
            ping_queue = ping_queue,
            dm_queue = dm_queue,
            logger = world_logger,
            datadir = world_data_dir
        )
        
        session = WorldSession(
            bot = self.bot,
            bot_client = bot_client,
            normal_channel_id = normal_channel_id,
            ping_channel_id = ping_channel_id,
            message_queue = message_queue,
            ping_queue = ping_queue,
            dm_queue = dm_queue,
            logger = world_logger,
            admin_ids = admin_ids,
            world_id = world_id
        )
        
        await session.start()
        session.tasks.append(asyncio.create_task(bot_client.run()))
        self.worlds[world_id] = session
        return 
    
    async def stop_world(self, world_id: str):
        session = self.worlds.get(world_id)
        if not session:
            return
        session.bot_client.player_db.save_db()
        session.bot_client.discord_db.save_db()
        await session.bot_client.stop()
        await session.stop()
        del self.worlds[world_id]
        
    async def delete_world(self, world_id: str):
        await self.stop_world(world_id)
        world_data_dir = os.path.join(self.datadir, world_id)
        if os.path.exists(world_data_dir):
            for root, dirs, files in os.walk(world_data_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(world_data_dir)
        
    async def stop_all_worlds(self):
        world_ids = list(self.worlds.keys())
        for world_id in world_ids:
            self.logger.info(f"Stopping world {world_id}")
            await self.stop_world(world_id)
        
    def get_world_from_channel(self, channel_id: int):
        for _ , session in self.worlds.items():
            if channel_id == session.normal_channel_id :
                return session
        return None
    
    async def load_worlds(self):
        if not os.path.exists(self.datadir):
            return
        for world_id in os.listdir(self.datadir):
            world_data_dir = os.path.join(self.datadir, world_id)
            if os.path.isdir(world_data_dir):
                config_path = os.path.join(world_data_dir, "config.json")
                if os.path.exists(config_path):
                    with open(config_path, "r", encoding="utf-8") as f:
                        config = json.load(f)
                        await self.create_world(world_data_dir, config)
        
class WorldSession:
    def __init__(
        self,
        bot,
        bot_client,
        normal_channel_id,
        ping_channel_id,
        message_queue,
        ping_queue,
        dm_queue,
        logger,
        admin_ids = [],
        world_id = None
    ):
        self.bot = bot
        self.bot_client = bot_client
        self.logger = logger
        self.normal_channel_id = normal_channel_id
        self.ping_channel_id = ping_channel_id
        self.message_queue = message_queue
        self.ping_queue = ping_queue
        self.dm_queue = dm_queue
        self.tasks = []
        self.admin_ids = admin_ids
        self.world_id = world_id

    async def discord_sender(self, channel, queue):
        while True:
            msg = await queue.get()
            try:
                await channel.send(msg)
            except Exception as e:
                self.logger.exception(e)
                
    async def dm_sender(self):
        while True:
            player, msg = await self.dm_queue.get()
            try:
                if player.discord_id:
                    if msg == "new_items":
                        await send_new_items(self.bot, self, player.discord_id)
                    else:
                        self.logger.warning(f"Player {player.player_name} has no discord id")
            except Exception as e:
                self.logger.exception(e)
                
    async def start(self):
        await self.bot.wait_until_ready()
        normal_channel = self.bot.get_channel(self.normal_channel_id)
        if normal_channel:
            self.tasks.append(asyncio.create_task(self.discord_sender(normal_channel, self.message_queue)))
            
        if self.ping_channel_id:
            ping_channel = self.bot.get_channel(self.ping_channel_id)
            if ping_channel:
                self.tasks.append(asyncio.create_task(self.discord_sender(ping_channel, self.ping_queue)))

        self.tasks.append(asyncio.create_task(self.dm_sender()))
        
    async def stop(self):
        for task in self.tasks:
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)