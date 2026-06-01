from archipelago.tracker_client import TrackerClient
from world.world_config import WorldConfigSelection
from utils.config import check_config
import discord
import asyncio
import os

async def is_admin(ctx, session):
    admin_ids = session.admin_ids
    if admin_ids == [] :
        return True # If no admin ids are specified, allow everyone to use admin commands
    return str(ctx.author.id) in session.admin_ids

def setup_admin_commands(bot) :
    
    @bot.command(name='admin', help='Admin command')
    async def admin_command(ctx):
        if not await is_admin(ctx, bot):
            await ctx.send("You don't have permission to use this command.")
            return
        await ctx.send('This is an admin command.')
    
    @bot.command(name='computeChecks')
    async def compute_checks(ctx):
        session = bot.world_manager.get_world_from_channel(ctx.channel.id)
        if session is None :
            bot.custom_logger.warning(f"Received message from channel {ctx.channel.id} but no world is associated to this channel.")
            await ctx.send("An error occurred while processing the command. Please try again later.")
            return
        if not await is_admin(ctx, session):
            await ctx.send("You don't have permission to use this command.")
            return
        await ctx.send("Computing checks for all players. This may take a while...")
        try :
            for player in session.bot_client.player_db.get_all_players():
                bot.custom_logger.info(f"Computing checks for player {player.player_name}")
                tracker_client = TrackerClient(session.bot_client.config, session.bot_client.logger, player.player_name)
                asyncio.create_task(tracker_client.run())
                await tracker_client.finished_event.wait()
                player.total_locations = tracker_client.total_locations
                player.checked_locations = tracker_client.checked_locations
            bot.custom_logger.info("Checks computed for all players")
            await ctx.send("Checks computed for all players")
        except Exception as e:
            bot.custom_logger.error(f"Error computing checks: {e}")
            await ctx.send(f"An error occurred while computing checks. Please try again later.")
            
    @bot.command(name="newWorld", help="Create a new world. Usage: !newWorld")
    async def new_world(ctx):
        data = {}
        view = WorldConfigSelection(author=ctx.author, data=data)
        await ctx.send(
            "Click to configure your world",
            view=view
        )
        await view.wait()
        data, valid = check_config(data)
        if not valid :
            await ctx.send("Invalid configuration, world creation cancelled. Please try again.")
            return
        
        datadir = os.getenv("DATA_DIRECTORY", "data")
        # Create a unique world ID 
        dt = discord.utils.utcnow()
        world_id = f"{ctx.author.id}_{int(discord.utils.time_snowflake(dt))}"
        world_data_dir = os.path.join(datadir, world_id)
        os.makedirs(world_data_dir, exist_ok=True)
        try:
            msg = await bot.world_manager.create_world(world_data_dir, data)
            if msg == "already_exists":
                await ctx.send("A world is already associated with the selected normal channel.\n\
Please delete the existing world before creating a new one or use a different normal channel in the configuration.")
                return
            await ctx.send(f"World created. You can now use the commands to interact with your world in {msg}.")
        except Exception as e:
            bot.custom_logger.error(f"Error creating world: {e}")
            await ctx.send(f"An error occurred while creating the world. Please try again later.")
            
    @bot.command(name="deleteWorld", help="Delete the world associated with the current channel. Usage: !deleteWorld")
    async def delete_world(ctx):
        session = bot.world_manager.get_world_from_channel(ctx.channel.id)
        if session is None :
            bot.custom_logger.warning(f"Received message from channel {ctx.channel.id} but no world is associated to this channel.")
            await ctx.send("No world is associated with this channel.")
            return
        if not await is_admin(ctx, session):
            await ctx.send("You don't have permission to use this command. Only the world admins can delete the world.")
            return
        try:
            await bot.world_manager.delete_world(session.world_id)
            await ctx.send("World deleted.")
        except Exception as e:
            bot.custom_logger.error(f"Error deleting world: {e}")
            await ctx.send(f"An error occurred while deleting the world. Please try again later.")
            
    @bot.command(name="listWorlds", help="List all worlds in the current discord server. Usage: !listWorlds")
    async def list_worlds(ctx):
        worlds = bot.world_manager.worlds
        if not worlds:
            await ctx.send("No worlds exist on this server.")
            return
        channel_link_list = []
        for session in worlds.values():
            normal_channel = bot.get_channel(session.normal_channel_id)
            if normal_channel and normal_channel.guild.id == ctx.guild.id:
                channel_link_list.append(f"https://discord.com/channels/{normal_channel.guild.id}/{normal_channel.id}")
        if not channel_link_list:
            await ctx.send("No worlds exist on this server.")
            return
        await ctx.send(f"There are {len(channel_link_list)} worlds on this server on the following channels:\n{chr(10).join(channel_link_list)}")

    @bot.command(name="isAdmin", help="Check if a user is an admin. Usage: !isAdmin")
    async def is_admin(ctx):
        session = bot.world_manager.get_world_from_channel(ctx.channel.id)
        if session is None:
            await ctx.send("No world is associated with this channel.")
            return False
        if ctx.author.id in session.admin_ids:
            await ctx.send("You are an admin.")
        else :
            await ctx.send("You are not an admin.")