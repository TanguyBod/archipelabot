from archipelago.tracker_client import TrackerClient
import asyncio

async def is_admin(ctx, session):
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