import discord
from discord.ext import commands
from discord_bot.commands import setup_commands
from discord_bot.admin_commands import setup_admin_commands
from discord_bot.events import setup_events
import os

def create_bot(logger) :
    # Create a single bot instance that will be used for all worlds, and will route messages to the correct world based on the channel they come from

    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True
    
    bot = commands.Bot(command_prefix=os.getenv("DISCORD_COMMAND_PREFIX"), intents=intents)
    bot.custom_logger = logger
    bot.app_token = os.getenv("DISCORD_APP_TOKEN")
    bot.remove_command('help')
    setup_commands(bot)
    setup_events(bot)
    setup_admin_commands(bot)
    return bot