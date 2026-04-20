import discord
from discord.ext import commands
from discord_bot.commands import setup_commands
from discord_bot.events import setup_events

def create_bot(tracker_client, message_queue, config):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True

    bot = commands.Bot(command_prefix="§", intents=intents)

    bot.tracker_client = tracker_client
    bot.messages_to_send = message_queue
    bot.normal_channel_id = config["DiscordConfig"]["normal_channel_id"]
    bot.admin_channel_id = config["DiscordConfig"]["admin_channel_id"]
    bot.app_token = config["DiscordConfig"]["app_token"]
    bot.config = config
    bot.remove_command('help')
    setup_commands(bot)
    setup_events(bot)

    return bot