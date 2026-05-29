from world.world_manager import WorldManager
from discord_bot.bot import create_bot
from dotenv import load_dotenv
import asyncio
import logging
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ArchiLink")
# Put discord logger to warning to avoid cluttering the console with discord debug messages
logging.getLogger("discord").setLevel(logging.WARNING) 

async def main():
    # Load .env file
    load_dotenv()
    datadir = os.getenv("DATA_DIRECTORY", "data")
    os.makedirs(datadir, exist_ok=True)
    discord_bot = create_bot(logger)
    world_manager = WorldManager(discord_bot, logger, datadir)
    discord_bot.world_manager = world_manager # Give the bot a reference to the world manager so it can route messages to the correct world based on the channel they come from
    
    try :
        await asyncio.gather(
            asyncio.create_task(discord_bot.start(os.getenv("DISCORD_APP_TOKEN")))
        )
    
    finally :
        logger.info("Shutting down, stopping all worlds...")
        await world_manager.stop_all_worlds()
        await discord_bot.close()
        
    
if __name__ == "__main__":
    asyncio.run(main())