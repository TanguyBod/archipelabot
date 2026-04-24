import discord
from discord.ext import commands
from discord_bot.commands import setup_commands
from discord_bot.events import setup_events

def create_bot(tracker_client, message_queue, ping_queue, dm_queue, config, logger):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True

    bot = commands.Bot(command_prefix=config["DiscordConfig"]["command_prefix"], intents=intents)
    bot.logger = logger
    bot.tracker_client = tracker_client
    bot.messages_to_send = message_queue
    bot.ping_queue = ping_queue
    bot.dm_queue = dm_queue
    bot.normal_channel_id = config["DiscordConfig"]["normal_channel_id"]
    bot.ping_channel_id = config["DiscordConfig"]["ping_channel_id"] or config["DiscordConfig"]["normal_channel_id"]
    bot.debug_channel_id = config["DiscordConfig"]["debug_channel_id"]
    bot.app_token = config["DiscordConfig"]["app_token"]
    bot.config = config
    bot.remove_command('help')
    setup_commands(bot)
    setup_events(bot)

    return bot