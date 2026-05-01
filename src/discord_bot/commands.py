from archipelago.hint_client import HintClient
from models.button import Button
from models.select import TodoView
from discord_bot.utils import *
from discord_bot.texts_flavors import *
import asyncio
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from io import BytesIO
import discord

def setup_commands(bot):
    
    @bot.command(name='hint')
    async def hint(ctx, *, hint: str):
        if await bad_channel_check(ctx, bot):
            return
        bot.logger.info(f"Hint command called with hint : {hint}")
        player = bot.bot_client.player_db.get_player_by_discord_id(ctx.author.id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            return
        else :
            try :
                hint_client_instance = HintClient(player.player_name, 
                                                player.player_game, 
                                                hint, 
                                                bot.bot_client,
                                                bot.config)
                asyncio.create_task(hint_client_instance.run())
                await hint_client_instance.finished_event.wait()
                # Send all messages in the queue :
                while not hint_client_instance.discord_bot_queue.empty() :
                    message = await hint_client_instance.discord_bot_queue.get()
                    try :
                        message, item = message
                        if "(found)" in message : # Do not add the possibility to add to todo list if already found
                            await ctx.send(message)
                            continue
                        button = Button(item, bot.bot_client)
                        message = await ctx.send(message, view=button)
                        button.message = message
                    except :
                        await ctx.send(message)
                # Terminate hint client
                await hint_client_instance.stop()
            except Exception as e :
                bot.logger.error(f"Error sending hint: {e}")
                await ctx.send(f"An error occurred while sending the hint. Please try again later.")

    @bot.command(name='players')
    async def players(ctx):
        if await bad_channel_check(ctx, bot):
            return
        players = bot.bot_client.player_db.get_all_players_names()
        await ctx.send("test")

    @bot.command(name='register')
    async def register(ctx, player_name: str) :
        if await bad_channel_check(ctx, bot):
            return
        # Check if player name is valid
        if player_name not in bot.bot_client.player_db.get_all_players_names() :
            await ctx.send(f"Player name {player_name} not found. Please check the spelling and try again.\n\
Available player names are : {', '.join(bot.bot_client.player_db.get_all_players_names())}")
        elif bot.bot_client.player_db.get_player_by_name(player_name).discord_id is not None :
            player = bot.bot_client.player_db.get_player_by_name(player_name)
            await ctx.send(f"Player {player_name} is already registered by {player.discord_id}.\nIf you think this is an error, please contact the administrator.")
        elif ctx.author.id in bot.bot_client.player_db.get_all_discord_ids() :
            player = bot.bot_client.player_db.get_player_by_discord_id(ctx.author.id)
            await ctx.send(f"You have already registered player {player.player_name} to your discord account. Please unregister it first using `!unregister {player.player_name}` command before registering another player.")
        else :
            # Get discord id of the user
            discord_id = ctx.author.id
            player = bot.bot_client.player_db.get_player_by_name(player_name)
            bot.bot_client.player_db.set_discord_id(player, discord_id)
            await ctx.send(f"Player {player_name} successfully registered to discord user {ctx.author.name}#{ctx.author.discriminator}.")

    @bot.command(name='unregister')
    async def unregister(ctx, player_name: str = None) :
        if await bad_channel_check(ctx, bot):
            return
        # Check if player name is valid
        if not player_name :
            player = bot.bot_client.player_db.get_player_by_discord_id(ctx.author.id)
            if player is None :
                await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            else :
                bot.bot_client.player_db.set_discord_id(player, None)
                await ctx.send(f"Player {player.player_name} successfully unregistered from discord user {ctx.author.name}#{ctx.author.discriminator}.")
        elif player_name not in bot.bot_client.player_db.get_all_players_names() :
            await ctx.send(f"Player name {player_name} not found. Please check the spelling and try again.\n\
Available player names are : {', '.join(bot.bot_client.player_db.get_all_players_names())}")
        else :
            player = bot.bot_client.player_db.get_player_by_name(player_name)
            if player.discord_id is None :
                await ctx.send(f"Player {player_name} is not registered to any discord user.")
            elif player.discord_id != ctx.author.id :
                await ctx.send(f"Player {player_name} is registered to another discord user. You cannot unregister it.\nIf you think this is an error, please contact the administrator.")
            else :
                bot.bot_client.player_db.set_discord_id(player, None)
                await ctx.send(f"Player {player_name} successfully unregistered from discord user {ctx.author.name}#{ctx.author.discriminator}.")

    @bot.command(name='new')
    async def new(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        await send_new_items(bot, discord_id)
            
    @bot.command(name='enableping')
    async def enableping(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        player = bot.bot_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            player.allow_ping = True
            await ctx.send(f"This discord bot can now ping you")
    
    @bot.command(name='disableping')
    async def disableping(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        player = bot.bot_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            player.allow_ping = False
            await ctx.send(f"This discord bot won't bother you anymore with pings")
            
    @bot.command(name='enablenewitems')
    async def enablenewitems(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        player = bot.bot_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            player.get_new_items_auto = True
            await ctx.send(f"You will now receive new items automatically in DM as soon as you start playing.")
            
    @bot.command(name='disablenewitems')
    async def disablenewitems(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        player = bot.bot_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            player.get_new_items_auto = False
            await ctx.send(f"You will now have to use `!new` command to check for new items received since the last time you checked.")

    @bot.command(name='todo')
    async def todo(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        bot.logger.info("todo command called")
        discord_id = ctx.author.id
        player = bot.bot_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        elif player.todolist == [] :
            flavor = get_empty_todolist_flavor()
            await ctx.send(flavor)
        else :
            bot.logger.info(f"Player found : {player.player_name} with {len(player.todolist)} items in todo list.")
            async with bot.bot_client.lock:
                items = list(player.todolist)
            flavor = get_todolist_flavor()
            msg = f"```ansi\n{flavor}\n\n"
            l1 = max(max(len(item.player_recieving.player_name) for item in items), len("For")) + 1
            l2 = max(max(len(item.item_name) for item in items), len("Item")) + 1
            l3 = max(max(len(item.location_name) for item in items), len("Location")) + 1
            msg += f"{'For'.ljust(l1)} || {'Item'.ljust(l2)} || {'Location'.ljust(l3)}\n"
            for item in items :
                msg += f"{ansi_ljust(item.player_recieving.name_colored, l1)} || {item.item_name.ljust(l2)} || {item.location_name.ljust(l3)}\n"
                if len(msg) > 1500 : # Discord message limit is 2000 characters, keep some margin
                    msg += "```"
                    await ctx.send(msg)
                    msg = "```ansi\n"
            msg += "```"
            if msg == f"```ansi\n```" :
                return
            view = TodoView(player, ctx.author.id)

            await ctx.send(
                msg,
                view=view
            )

        
    @bot.command(name="clearTodo")
    async def clear_todo(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        player = bot.bot_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            async with bot.bot_client.lock:
                player.todolist.clear()
            msg = get_clear_todolist_flavor()
            await ctx.send(msg)
            
    @bot.command(name='removeTodo')
    async def remove_todo(ctx, *, item_name: str) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        player = bot.bot_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            async with bot.bot_client.lock:
                item_to_remove = None
                for item in player.todolist :
                    if item.item_name.lower() == item_name.lower() :
                        item_to_remove = item
                        break
                if item_to_remove is None :
                    await ctx.send(f"Item {item_name} not found in your todo list.")
                else :
                    player.todolist.remove(item_to_remove)
                    await ctx.send(f"Item {item_name} removed from your todo list.")
                    
    @bot.command(name='wishlist')
    async def wishlist(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        player = bot.bot_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        wishlist = []
        for other_player in bot.bot_client.player_db.get_all_players() :
            if other_player.player_name == player.player_name :
                continue
            async with bot.bot_client.lock:
                for item in other_player.todolist:
                    if item.player_recieving.player_name == player.player_name :
                        wishlist.append(item)
        if wishlist == [] :
            await ctx.send(f"You do not have any item in your wishlist.")
        else :
            flavor = get_wishlist_flavor()
            msg = f"```ansi\n{flavor}\n\n"
            l1 = max(max(len(item.player_sending.player_name) for item in wishlist), len("From")) + 1
            l2 = max(max(len(item.item_name) for item in wishlist), len("Item")) + 1
            l3 = max(max(len(item.location_name) for item in wishlist), len("Location")) + 1
            msg += f"{'From'.ljust(l1)} || {'Item'.ljust(l2)} || {'Location'.ljust(l3)}\n"
            for item in wishlist :
                msg += f"{ansi_ljust(item.player_sending.name_colored, l1)} || {item.item_name.ljust(l2)} || {item.location_name.ljust(l3)}\n"
                if len(msg) > 1500 : # Discord message limit is 2000 characters, keep some margin
                    msg += "```"
                    await ctx.send(msg)
                    msg = "```ansi\n"
            msg += "```"
            if msg == f"```ansi\n```" :
                return
            await ctx.send(msg)
            
    @bot.command(name='wastedOnArchipelago')
    async def wastedOnArchipelago(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        player = bot.bot_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            time_played = player.time_played
            hours = int(time_played // 3600)
            minutes = int((time_played % 3600) // 60)
            seconds = int(time_played % 60)
            await ctx.send(f"You have wasted {hours} hours, {minutes} minutes and {seconds} seconds in this Archipelago Multiworld.")
            
    @bot.command(name='deaths')
    async def deaths(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        player = bot.bot_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            await ctx.send(f"You have died {len(player.deaths)} times.")
    
    @bot.command(name='deathgraph')
    async def deathgraph(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        player = bot.bot_client.player_db.get_player_by_discord_id(discord_id)
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            if player.deaths == [] :
                await ctx.send(f"You have not died yet. Congratulations !")
            else :
                deaths_minutes = [t / 60 for t in player.deaths]
                cumulative_deaths = list(range(1, len(deaths_minutes) + 1))
                deaths_minutes = [0] + deaths_minutes
                cumulative_deaths = [0] + cumulative_deaths
                plt.figure(figsize=(10,5))
                plt.step(deaths_minutes, cumulative_deaths, where='post')
                plt.scatter(deaths_minutes, cumulative_deaths)
                plt.title(f'{player.player_name} death graph')
                plt.xlabel('Time played (minutes)')
                plt.ylabel('Number of Deaths')
                buf = BytesIO()
                plt.savefig(buf, format='png')
                buf.seek(0)
                await ctx.send(file=discord.File(buf, filename='death_graph.png'))
                
    @bot.command(name='globaldeaths')
    async def globaldeaths(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        deaths_dict = {}
        for player in bot.bot_client.player_db.get_all_players() :
            deaths_dict[player.player_name] = len(player.deaths)
        plt.figure(figsize=(10,5))
        plt.bar(deaths_dict.keys(), deaths_dict.values())
        plt.title('Global Deaths')
        plt.xlabel('Player')
        plt.ylabel('Number of Deaths')
        plt.xticks(rotation=45)
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        await ctx.send(file=discord.File(buf, filename='global_deaths.png'))
        
    @bot.command(name='progressGraph')
    async def progress_graph(ctx):
        if await bad_channel_check(ctx, bot):
            return
        percentage_dict = {}; checks_dict = {}
        for player in bot.bot_client.player_db.get_all_players() :
            if player.total_locations <= 0 :
                await ctx.send(f"Error retrieving total locations for player {player.player_name}. Cannot compute progress graph.")
                return
            percentage = (player.checked_locations / player.total_locations * 100) if player.total_locations > 0 else 0
            checks_dict[player.player_name] = player.checked_locations
            percentage_dict[player.player_name] = percentage
        num_players = len(percentage_dict)
        plt.figure(figsize=(max(10, num_players*0.5), 8))
        values = list(percentage_dict.values())
        norm = mcolors.Normalize(vmin=0, vmax=100)
        cmap = cm.get_cmap('coolwarm')
        colors = [cmap(norm(v)) for v in values]
        bars = plt.bar(percentage_dict.keys(), percentage_dict.values(), color=colors)
        # Add value labels on top of bars
        for bar, player_name in zip(bars, percentage_dict.keys()):
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height + 1,
                str(checks_dict[player_name]),
                ha='center',
                va='bottom',
                fontsize=9
            )
        plt.title('Progress Graph')
        plt.xlabel('Player')
        plt.ylabel('Percentage of checked locations')
        plt.xticks(rotation=45)
        buf = BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        await ctx.send(file=discord.File(buf, filename='progress_graph.png'))

    # Updated `help` Command


    @bot.command(name='help')
    async def help(ctx, command: str = None):
        if await bad_channel_check(ctx, bot):
            return

        commands_help = {
            "register": {
                "usage": "`!register <player_name>`",
                "description": "Register your Discord account to a player.",
                "details": (
                    "You will receive notifications about this player's items and gain access "
                    "to player-specific commands such as `!todo`, `!wishlist`, and `!new`.\n\n"
                    "Example: `!register Alice`"
                )
            },
            "unregister": {
                "usage": "`!unregister [player_name]`",
                "description": "Unregister your Discord account from a player.",
                "details": (
                    "If no player name is provided, you will be unregistered from your current player.\n\n"
                    "Examples:\n"
                    "`!unregister`\n"
                    "`!unregister Alice`"
                )
            },
            "players": {
                "usage": "`!players`",
                "description": "Display all players in the multiworld.",
                "details": "Useful to verify the exact spelling of player names."
            },
            "hint": {
                "usage": "`!hint <text>`",
                "description": "Send a hint query to the tracker.",
                "details": (
                    "Recognized hints may provide buttons to add items to todo lists.\n\n"
                    "Example: `!hint City Crest`"
                )
            },
            "new": {
                "usage": "`!new`",
                "description": "Check newly received items.",
                "details": "New items are sent through DM to avoid channel spam."
            },
            "enableping": {
                "usage": "`!enableping`",
                "description": "Allow the bot to ping you.",
                "details": "You may be pinged when another player finds an item relevant to your todo list."
            },
            "disableping": {
                "usage": "`!disableping`",
                "description": "Disable bot pings.",
                "details": "The bot won't ping you anymore."
            },
            "enablenewitems": {
                "usage": "`!enablenewitems`",
                "description": "Enable automatic DM notifications for new items.",
                "details": "You will automatically receive newly collected items in DM when connecting your game."
            },
            "disablenewitems": {
                "usage": "`!disablenewitems`",
                "description": "Disable automatic DM notifications for new items.",
                "details": "You will need to use `!new` manually to check for received items."
            },
            "todo": {
                "usage": "`!todo`",
                "description": "Show your todo list.",
                "details": "Displays all tracked items you still need to collect or verify."
            },
            "cleartodo": {
                "usage": "`!clearTodo`",
                "description": "Clear your todo list.",
                "details": "Removes every item from your current todo list."
            },
            "removetodo": {
                "usage": "`!removeTodo <item_name>`",
                "description": "Remove a specific item from your todo list.",
                "details": "Example: `!removeTodo Hookshot`"
            },
            "wishlist": {
                "usage": "`!wishlist`",
                "description": "Display items other players have marked for you.",
                "details": "Shows all wishlist items targeting your player."
            },
            "wastedonarchipelago": {
                "usage": "`!wastedOnArchipelago`",
                "description": "Display your total playtime.",
                "details": "Shows the total time spent in the multiworld session."
            },
            "deaths": {
                "usage": "`!deaths`",
                "description": "Display your total death count.",
                "details": "Shows how many times you died during the session."
            },
            "deathgraph": {
                "usage": "`!deathgraph`",
                "description": "Generate a graph of your deaths over time.",
                "details": "Displays cumulative deaths based on playtime progression."
            },
            "globaldeaths": {
                "usage": "`!globaldeaths`",
                "description": "Display total deaths for all players.",
                "details": "Generates a comparison graph between all players."
            },
            "progressgraph": {
                "usage": "`!progressGraph`",
                "description": "Generate a progression graph for all players.",
                "details": "Shows completion percentages and checked locations for every player."
            },
            "help": {
                "usage": "`!help [command]`",
                "description": "Display help information.",
                "details": "Use without arguments to list all commands or specify a command for detailed help."
            }
        }

        if command is None:
            msg = "**Available commands:**\n\n"

            for cmd_name, data in commands_help.items():
                msg += f"{data['usage']} : {data['description']}\n"

            msg += "\nUse `!help <command>` for detailed information about a specific command."
            await ctx.send(msg)
            return

        command = command.lower()

        if command not in commands_help:
            await ctx.send(
                f"Command `{command}` not found. Use `!help` to see all available commands."
            )
            return

        data = commands_help[command]

        msg = (
            f"**{data['usage']}**\n\n"
            f"{data['description']}\n\n"
            f"{data['details']}"
        )

        await ctx.send(msg)

            
            
    