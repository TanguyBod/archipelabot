from archipelago.hint_client import HintClient
from utils.colors import get_ansi_color_from_flag
import asyncio

def setup_commands(bot):
    
    @bot.command()
    async def hint(ctx, hint: str):
        player = bot.tracker_client.player_db.get_player_by_discord_id(ctx.author.id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            return
        else :
            try :
                hint_client_instance = HintClient(player.player_name, 
                                                player.player_game, 
                                                hint, 
                                                bot.tracker_client,
                                                bot.config)
                asyncio.create_task(hint_client_instance.run())
                await hint_client_instance.finished_event.wait()
                # Send all messages in the queue :
                while not hint_client_instance.discord_bot_queue.empty() :
                    message = await hint_client_instance.discord_bot_queue.get()
                    await ctx.send(message)
                # Terminate hint client
                await hint_client_instance.stop()
            except Exception as e :
                print(f"Error sending hint: {e}")
                await ctx.send(f"An error occurred while sending the hint. Please try again later.")

    @bot.command()
    async def players(ctx):
        players = bot.tracker_client.player_db.get_all_players_names()
        await ctx.send("test")

    @bot.command()
    async def register(ctx, player_name: str) :
        # Check if player name is valid
        if player_name not in bot.tracker_client.player_db.get_all_players_names() :
            await ctx.send(f"Player name {player_name} not found. Please check the spelling and try again.\n\
    Available player names are : {', '.join(bot.tracker_client.player_db.get_all_players_names())}")
        elif bot.tracker_client.player_db.get_player_by_name(player_name).discord_id is not None :
            player = bot.tracker_client.player_db.get_player_by_name(player_name)
            await ctx.send(f"Player {player_name} is already registered by {player.discord_id}.\nIf you think this is an error, please contact the administrator.")
        elif ctx.author.id in bot.tracker_client.player_db.get_all_discord_ids() :
            player = bot.tracker_client.player_db.get_player_by_discord_id(ctx.author.id)
            await ctx.send(f"You have already registered player {player.player_name} to your discord account. Please unregister it first using `!unregister {player.player_name}` command before registering another player.")
        else :
            # Get discord id of the user
            discord_id = ctx.author.id
            player = bot.tracker_client.player_db.get_player_by_name(player_name)
            bot.tracker_client.player_db.set_discord_id(player, discord_id)
            await ctx.send(f"Player {player_name} successfully registered to discord user {ctx.author.name}#{ctx.author.discriminator}.")

    @bot.command()
    async def unregister(ctx, player_name: str) :
        # Check if player name is valid
        if player_name not in bot.tracker_client.player_db.get_all_players_names() :
            await ctx.send(f"Player name {player_name} not found. Please check the spelling and try again.\n\
    Available player names are : {', '.join(bot.tracker_client.player_db.get_all_players_names())}")
        else :
            player = bot.tracker_client.player_db.get_player_by_name(player_name)
            if player.discord_id is None :
                await ctx.send(f"Player {player_name} is not registered to any discord user.")
            elif player.discord_id != ctx.author.id :
                await ctx.send(f"Player {player_name} is registered to another discord user. You cannot unregister it.\nIf you think this is an error, please contact the administrator.")
            else :
                bot.tracker_client.player_db.set_discord_id(player, None)
                await ctx.send(f"Player {player_name} successfully unregistered from discord user {ctx.author.name}#{ctx.author.discriminator}.")

    @bot.command()
    async def new(ctx) :
        discord_id = ctx.author.id
        player = bot.tracker_client.player_db.get_player_by_discord_id(discord_id)
        user = await bot.fetch_user(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
        elif len(player.new_items) == 0 :
            print(f"Player found : {player.player_name} but no new items to send.")
            # DM player if no new items, to avoid spamming the channel
            # Check if bot can DM the user
            if user.dm_channel is None :
                await user.create_dm() 
            await user.dm_channel.send("You have not received any new items since the last time you checked.")
        else :
            if user.dm_channel is None :
                await user.create_dm()
            print(f"Player found : {player.player_name} with {len(player.new_items)} new items to send.")
            msg = "```ansi\n"
            async with bot.tracker_client.lock:
                items = list(player.new_items)
                player.new_items.clear()
            l1 = len(player.player_name) + 2
            l2 = max(len(item.item_name) for item in items) + 2
            l3 = max(len(item.player_sending.player_name) for item in items) + 2
            l4 = max(len(item.location_name) for item in items) + 2
            msg += f"{'You'.ljust(l1)} || {'Item'.ljust(l2)} || {'Sender'.ljust(l3)} || {'Location'.ljust(l4)}\n"
            for item in items :
                color = await get_ansi_color_from_flag(item.flag)
                msg += f"{player.player_name.ljust(l1)} || \u001b[0;{color}m{item.item_name.ljust(l2)}\u001b[0m || {item.player_sending.player_name.ljust(l3)} || {item.location_name.ljust(l4)}\n"
                if len(msg) > 1900 : # Discord message limit is 2000 characters, keep some margin
                    msg += "```"
                    await user.dm_channel.send(msg)
                    msg = "```ansi\n"
            msg += "```"
            await user.dm_channel.send(msg)
            
    @bot.command()
    async def enableping(ctx) :
        discord_id = ctx.author.id
        player = bot.tracker_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            player.allow_ping = True
            await ctx.send(f"This discord bot can now ping you")
    
    @bot.command()
    async def disableping(ctx) :
        discord_id = ctx.author.id
        player = bot.tracker_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            player.allow_ping = False
            await ctx.send(f"This discord bot won't bother you anymore with pings")

    @bot.command()
    async def todo(ctx) :
        discord_id = ctx.author.id
        player = bot.tracker_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        elif player.todolist == [] :
            await ctx.send(f"All is good, nobody needs you")
        else :
            async with bot.tracker_client.lock:
                items = list(player.todolist)
            msg = "```ansi\n Behold: the highly negotiated list of items your teammates absolutely needed\n\n"
            l1 = max(len(item.player_recieving.player_name) for item in items)
            l2 = max(len(item.item_name) for item in items) + 2
            l3 = max(len(item.location_name) for item in items) + 2
            msg += f"{'For'.ljust(l1)} || {'Item'.ljust(l2)} || {'Location'.ljust(l3)}\n"
            for item in items :
                msg += f"{item.player_recieving.player_name.ljust(l1)} || {item.item_name.ljust(l2)} || {item.location_name.ljust(l3)}"
                if len(msg) > 1900 : # Discord message limit is 2000 characters, keep some margin
                    msg += "```"
                    await ctx.send(msg)
                    msg = "```ansi\n"
            msg += "```"
            await ctx.send(msg)