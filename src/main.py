import asyncio
import os
from utils.config import load_config
from archipelago.bot_client import BotClient
from discord_bot.bot import create_bot
from asyncio import Queue
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Archipelabot")

async def main():
    config = load_config()
    message_queue = Queue(maxsize=2000)
    ping_queue = Queue(maxsize=2000)
    dm_queue = Queue(maxsize=2000)

    bot_client = BotClient(config, message_queue, ping_queue, dm_queue, logger)
    bot = create_bot(bot_client, message_queue, ping_queue, dm_queue, config, logger)

    try:
        await asyncio.gather(
            bot_client.run(),
            bot.start(config["DiscordConfig"]["app_token"])
        )

    finally:
        logger.info("\nShutting down cleanly...")
        # Make sure data folder exists
        os.makedirs(config["DatabaseConfig"]["data_directory"], exist_ok=True)
        bot_client.player_db.save_db(f"{config['DatabaseConfig']['data_directory']}/players.json")
        await bot_client.stop()
        await bot.close()

if __name__ == "__main__":
    asyncio.run(main())