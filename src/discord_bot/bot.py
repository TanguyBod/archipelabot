import discord
from discord.ext import commands
from discord_bot.commands import setup_commands
from discord_bot.admin_commands import setup_admin_commands
from discord_bot.events import setup_events

def create_bot(bot_client, message_queue, ping_queue, dm_queue, config, logger):
    intents = discord.Intents.default()
    intents.message_content = True
    intents.reactions = True

    bot = commands.Bot(command_prefix=config["DiscordConfig"]["command_prefix"], intents=intents)
    bot.logger = logger
    bot.bot_client = bot_client
    bot.messages_to_send = message_queue
    bot.ping_queue = ping_queue
    bot.dm_queue = dm_queue
    bot.normal_channel_id = config["DiscordConfig"]["normal_channel_id"]
    bot.ping_channel_id = config["DiscordConfig"]["ping_channel_id"] or config["DiscordConfig"]["normal_channel_id"]
    bot.debug_channel_id = config["DiscordConfig"]["debug_channel_id"]
    bot.app_token = config["DiscordConfig"]["app_token"]
    bot.admins = config["DiscordConfig"]["admin_ids"]
    if bot.admins == [] or bot.admins is None:
        bot.logger.warning("No admin IDs specified in config. Admin commands will not be runnable.") 
    bot.config = config
    bot.remove_command('help')
    setup_commands(bot)
    setup_admin_commands(bot)
    setup_events(bot)

    return bot