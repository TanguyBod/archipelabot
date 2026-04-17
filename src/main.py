import asyncio
from utils.config import load_config
from archipelago.tracker_client import TrackerClient
from discord_bot.bot import create_bot
from asyncio import Queue

async def main():
    config = load_config()

    message_queue = Queue(maxsize=2000)

    tracker_client = TrackerClient(config, message_queue)

    bot = create_bot(tracker_client, message_queue, config)

    await asyncio.gather(
        tracker_client.run(),
        bot.start(config["DiscordConfig"]["app_token"])
    )

if __name__ == "__main__":
    asyncio.run(main())