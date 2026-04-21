from archipelago.hint_client import HintClient
from models.button import Button
from utils.colors import get_ansi_color_from_flag
from discord_bot.texts_flavors import get_clear_todolist_flavor, get_todolist_flavor, get_empty_todolist_flavor
import asyncio

def setup_commands(bot):
    
    @bot.command()
    async def hint(ctx, *, hint: str):
        bot.logger.info(f"Hint command called with hint : {hint}")
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
                    try :
                        message, item = message
                        button = Button(item, bot.tracker_client)
                        message = await ctx.send(message, view=button)
                        button.message = message
                    except :
                        await ctx.send(message)
                # Terminate hint client
                await hint_client_instance.stop()
            except Exception as e :
                bot.logger.error(f"Error sending hint: {e}")
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
    async def unregister(ctx, player_name: str = None) :
        # Check if player name is valid
        if not player_name :
            player = bot.tracker_client.player_db.get_player_by_discord_id(ctx.author.id)
            if player is None :
                await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            else :
                bot.tracker_client.player_db.set_discord_id(player, None)
                await ctx.send(f"Player {player.player_name} successfully unregistered from discord user {ctx.author.name}#{ctx.author.discriminator}.")
        elif player_name not in bot.tracker_client.player_db.get_all_players_names() :
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
            bot.logger.debug(f"Player found : {player.player_name} but no new items to send.")
            # DM player if no new items, to avoid spamming the channel
            # Check if bot can DM the user
            if user.dm_channel is None :
                await user.create_dm() 
            await user.dm_channel.send("You have not received any new items since the last time you checked.")
        else :
            if user.dm_channel is None :
                await user.create_dm()
            bot.logger.debug(f"Player found : {player.player_name} with {len(player.new_items)} new items to send.")
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
        bot.logger.debug("todo command called")
        discord_id = ctx.author.id
        player = bot.tracker_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        elif player.todolist == [] :
            flavor = get_empty_todolist_flavor()
            await ctx.send(flavor)
        else :
            bot.logger.info(f"Player found : {player.player_name} with {len(player.todolist)} items in todo list.")
            async with bot.tracker_client.lock:
                items = list(player.todolist)
            bot.logger.debug(f"Items : {items}")
            flavor = get_todolist_flavor()
            msg = f"```ansi\n{flavor}\n\n"
            bot.logger.debug(f"First item : {items[0].__str__()}")
            l1 = max(len(item.player_recieving.player_name) for item in items)
            bot.logger.debug(f"l1 : {l1}")
            l2 = max(len(item.item_name) for item in items) + 2
            bot.logger.debug(f"l2 : {l2}")
            l3 = max(len(item.location_name) for item in items) + 2
            bot.logger.debug(f"l3 : {l3}")
            msg += f"{'For'.ljust(l1)} || {'Item'.ljust(l2)} || {'Location'.ljust(l3)}\n"
            for item in items :
                bot.logger.debug(f"Item : {item} added")
                msg += f"{item.player_recieving.player_name.ljust(l1)} || {item.item_name.ljust(l2)} || {item.location_name.ljust(l3)}\n"
                if len(msg) > 1900 : # Discord message limit is 2000 characters, keep some margin
                    msg += "```"
                    await ctx.send(msg)
                    msg = "```ansi\n"
            msg += "```"
            await ctx.send(msg)

        
    @bot.command()
    async def clear_todo(ctx) :
        discord_id = ctx.author.id
        player = bot.tracker_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            async with bot.tracker_client.lock:
                player.todolist.clear()
            msg = get_clear_todolist_flavor()
            await ctx.send(msg)

    @bot.command()
    async def help(ctx, command: str = None) :
        if command is None :
            msg = """**Available commands:**\n
`!register <player_name>` : Register your discord account to a player. You will receive notifications about this player's items and you can use other commands to see the player's todo list and new items.\n
`!unregister <Optional : player_name>` : Unregister your discord account from a player. If player_name is not provided, it will unregister from the player you are currently registered to. If player_name is provided, it will unregister from that player if you are registered to it.\n
`!players` : List all players in the tracker.\n
`!hint <hint>` : Send a hint to the tracker. The hint will be processed and you'll be able to add the item to the sender's todo list.\n
`!new` : Check for new items received since the last time you checked. The items will be sent to you in a DM to avoid spamming the channel.\n
`!enableping` : Allow the bot to ping you when (i.e. in a todolist) an item you wanted is sent by another player.\n
`!disableping` : Disallow the bot to ping you when an item you wanted (i.e. in a todolist) is sent by another player.\n
`!todo` : Show your current todo list.\n
`!clear_todo` : Clear your current todo list.\n
`!help <command>` : Show this message or, if a command is provided, show detailed information about that command.
"""
            await ctx.send(msg)
        else :
            command = command.lower()
            if command == "register" :
                msg = """`!register <player_name>` : Register your discord account to a player. You will receive notifications about this player's items and you can use other commands to see the player's todo list and new items.\n
Example : `!register Alice` will register you to the player named Alice. You can only be registered to one player at a time. If you want to register to another player, you need to unregister first using `!unregister` command."""
            elif command == "unregister" :
                msg = """`!unregister <Optional : player_name>` : Unregister your discord account from a player. If player_name is not provided, it will unregister from the player you are currently registered to. If player_name is provided, it will unregister from that player if you are registered to it.\n
Example : `!unregister` will unregister you from the player you are currently registered to. `!unregister Alice` will unregister you from the player named Alice if you are registered to it."""
            elif command == "players" :
                msg = """`!players` : List all players in the tracker.\n
Example : `!players` will list all players in the tracker. This command is useful to know the exact spelling of the player names to use them in other commands."""
            elif command == "hint" :
                msg = """`!hint <hint>` : Send a hint to the tracker. The hint will be processed and you'll be able to add the item to the sender's todo list.\n
Example : `!hint I found a red chest in the forest` will send the hint "I found a red chest in the forest" to the tracker. If the hint is recognized as an item, you will receive a message with the item name and a button to add it to the sender's todo list."""
            elif command == "new" :
                msg = """`!new` : Check for new items received since the last time you checked. The items will be sent to you in a DM to avoid spamming the channel.\n
Example : `!new` will check for new items received since the last time you checked and send them to you in a DM."""
            elif command == "enableping" :
                msg = """`!enableping` : Allow the bot to ping you when (i.e. in a todolist) an item you wanted is sent by another player.\n
Example : `!enableping` will allow the bot to ping you when an item you wanted is sent by another player."""
            elif command == "disableping" :
                msg = """`!disableping` : Disallow the bot to ping you when an item you wanted (i.e. in a todolist) is sent by another player.\n
Example : `!disableping` will disallow the bot to ping you when an item you wanted is sent by another player."""
            elif command == "todo" :
                msg = """`!todo` : Show your current todo list.\n
Example : `!todo` will show your current todo list. The todo list contains items that you wanted and that other players have sent to you. If the todo list is empty, it will show a message saying that your todo list is empty."""
            elif command == "clear_todo" :
                msg = """`!clear_todo` : Clear your current todo list.\n
Example : `!clear_todo` will clear your current todo list. Use this command when you have received the items in your todo list and want to clear it."""
            else :
                msg = f"Command {command} not found. Use `!help` command to see the list of available commands."
            await ctx.send(msg)