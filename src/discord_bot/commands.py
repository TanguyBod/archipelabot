from archipelago.hint_client import HintClient
from models.discord_profil import DiscordProfile
from models.button import Button
from utils.colors import get_ansi_color_from_flag
from discord_bot.texts_flavors import *
import asyncio
import re
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from io import BytesIO
import discord
from world.world import EntryView

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(s):
    return ANSI_ESCAPE.sub('', s)

def ansi_ljust(s, width):
    return s + " " * (width - len(strip_ansi(s)))

async def bad_channel_check(ctx, bot) :
    if ctx.channel is not None and ctx.channel.id != bot.normal_channel_id :
        bot.logger.warning(f"Current channel id is {ctx.channel.id} but normal channel id is {bot.normal_channel_id}.")
        await ctx.send("""Please use this command in the normal channel to avoid spamming other channels.\nIf you think this is an error, please contact the administrator.""")
        return True
    return False

async def send_new_items(bot, player_id) :
    player = bot.bot_client.player_db.get_player_by_discord_id(player_id)
    user = await bot.fetch_user(player_id)
    if user.dm_channel is None :
        await user.create_dm() 
    if player is None :
        bot.logger.error(f"Player with discord id {player_id} not found.")
        return
    elif len(player.new_items) == 0 :
        bot.logger.info(f"Player found : {player.player_name} but no new items to send.")
        # DM player if no new items, to avoid spamming the channel
        await user.dm_channel.send("You have not received any new items since the last time you checked.")
    else :
        bot.logger.info(f"Player found : {player.player_name} with {len(player.new_items)} new items to send.")
        msg = "```ansi\n"
        async with bot.bot_client.lock:
            items = list(player.new_items)
            player.new_items.clear()
        l1 = max(len("You"), len(player.player_name)) + 1
        l2 = max(len("Item"), max(len(item.item_name) for item in items)) + 1
        l3 = max(len("Sender"), max(len(item.player_sending.player_name) for item in items)) + 1
        l4 = max(len("Location"), max(len(item.location_name) for item in items)) + 1
        msg += f"{'You'.ljust(l1)} || {'Item'.ljust(l2)} || {'Sender'.ljust(l3)} || {'Location'.ljust(l4)}\n"
        for item in items :
            color = await get_ansi_color_from_flag(item.flag)
            msg += f"{ansi_ljust(player.name_colored, l1)} || \u001b[0;{color}m{item.item_name.ljust(l2)}\u001b[0m || {ansi_ljust(item.player_sending.name_colored, l3)} || {item.location_name.ljust(l4)}\n"
            if len(msg) > 1500 : # Discord message limit is 2000 characters, keep some margin
                msg += "```"
                await user.dm_channel.send(msg)
                msg = "```ansi\n"
        msg += "```"
        if msg == f"```ansi\n```" :
            return
        await user.dm_channel.send(msg)


def setup_commands(bot):
    
    @bot.command()
    async def newWorld(ctx):
        await ctx.send(
            "Click to configure your world",
            view=EntryView()
        )
    
    @bot.command(name='hint')
    async def hint(ctx, *, hint: str):
        if await bad_channel_check(ctx, bot):
            return
        bot.logger.info(f"Hint command called with hint : {hint}")
        discord_profil = bot.bot_client.discord_db.get_discord_profile(ctx.author.id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            return
        player = discord_profil.current_slot
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
        await ctx.send(f"Players in this multiworld are : {', '.join(players)}")

    @bot.command(name='register')
    async def register(ctx, *, player_name: str) :
        if await bad_channel_check(ctx, bot):
            return
        # Check if player name is valid
        if player_name not in bot.bot_client.player_db.get_all_players_names() :
            await ctx.send(f"Player name {player_name} not found. Please check the spelling and try again.\n\
Available player names are : {', '.join(bot.bot_client.player_db.get_all_players_names())}")
        elif bot.bot_client.player_db.get_player_by_name(player_name).discord_id is not None :
            player = bot.bot_client.player_db.get_player_by_name(player_name)
            await ctx.send(f"Player {player_name} is already registered by {player.discord_id}.\nIf you think this is an error, please contact the administrator.")
        else :
            discord_profil = bot.bot_client.discord_db.get_discord_profile(ctx.author.id)
            if discord_profil is None :
                discord_profil = DiscordProfile(ctx.author.name, ctx.author.id)
            player = bot.bot_client.player_db.get_player_by_name(player_name)
            # Link player and discord profile
            discord_profil.slots.append(player)
            discord_profil.current_slot = player
            bot.bot_client.discord_db.add_discord_profile(discord_profil)
            bot.bot_client.player_db.set_discord_id(player, discord_profil.id)
            await ctx.send(f"Player {player_name} successfully registered to discord user {ctx.author.name}#{ctx.author.discriminator}.\n\
You are currently registered to : {', '.join([p.player_name for p in discord_profil.slots])}")

    @bot.command(name='unregister')
    async def unregister(ctx, *, player_name: str = None) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        registered_players = [p.player_name for p in discord_profil.slots] if discord_profil else []
        if registered_players == [] :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            return
        elif player_name is not None and player_name not in registered_players :
            await ctx.send(f"You are not registered to player {player_name}. You are currently registered to : {', '.join(registered_players)}.")
        elif player_name is not None and player_name in registered_players :
            player = bot.bot_client.player_db.get_player_by_name(player_name)
            # Unlink player and discord profile
            discord_profil.slots.remove(player)
            bot.bot_client.player_db.set_discord_id(player, None)
            await ctx.send(f"Player {player_name} successfully unregistered from discord user {ctx.author.name}#{ctx.author.discriminator}.")
        else :
            # Unregister from all players
            for player in discord_profil.slots:
                bot.bot_client.player_db.set_discord_id(player, None)
            discord_profil.slots.clear()
            await ctx.send(f"All players successfully unregistered from discord user {ctx.author.name}#{ctx.author.discriminator}.")
            
    @bot.command(name='current')
    async def current(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None or discord_profil.slots == [] :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            return
        else :
            current_player = discord_profil.current_slot
            await ctx.send(f"You are currently tracking {current_player.player_name}. Use `!switch` command to switch to another player if you are registered to multiple players.")
    
    @bot.command(name='switch')
    async def switch(ctx, *, player_name: str = None) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None or discord_profil.slots == [] :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            return
        elif player_name == None :
            # Switch to next slot in the list
            current_player = discord_profil.current_slot
            if current_player is None :
                discord_profil.current_slot = discord_profil.slots[0]
                await ctx.send(f"Successfully switched to player {discord_profil.slots[0].player_name}.")
            else :
                current_index = discord_profil.slots.index(current_player)
                next_index = (current_index + 1) % len(discord_profil.slots)
                discord_profil.current_slot = discord_profil.slots[next_index]
                await ctx.send(f"Successfully switched to player {discord_profil.slots[next_index].player_name}.")
        elif player_name not in [p.player_name for p in discord_profil.slots] :
            await ctx.send(f"You are not registered to player {player_name}. You are currently registered to : {', '.join([p.player_name for p in discord_profil.slots])}.")
        else :
            player = bot.bot_client.player_db.get_player_by_name(player_name)
            discord_profil.current_slot = player
            await ctx.send(f"Successfully switched to player {player_name}.")

    @bot.command(name='new')
    async def new(ctx, all: str = None) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None or discord_profil.slots == [] :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            return
        elif all == "all" :
            for player in discord_profil.slots :
                await send_new_items(bot, player.discord_id)
        else :
            current_player = discord_profil.current_slot
            await send_new_items(bot, current_player.discord_id)
            
    @bot.command(name='enableping')
    async def enableping(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        registered_players = [p.player_name for p in discord_profil.slots] if discord_profil else []
        if registered_players == [] :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            for player in discord_profil.slots :
                player.allow_ping = True
            await ctx.send(f"This discord bot will now ping you when another player finds an item relevant to your todo list.")
    
    @bot.command(name='disableping')
    async def disableping(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        registered_players = [p.player_name for p in discord_profil.slots] if discord_profil else []
        if registered_players == [] :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            for player in discord_profil.slots :
                player.allow_ping = False
            await ctx.send(f"This discord bot won't bother you anymore with pings")
            
    @bot.command(name='enablenewitems')
    async def enablenewitems(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        registered_players = [p.player_name for p in discord_profil.slots] if discord_profil else []
        if registered_players == [] :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            for player in discord_profil.slots :
                player.get_new_items_auto = True
            await ctx.send(f"You will now receive new items automatically in DM as soon as you start playing.")
            
    @bot.command(name='disablenewitems')
    async def disablenewitems(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        registered_players = [p.player_name for p in discord_profil.slots] if discord_profil else []
        if registered_players == [] :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            for player in discord_profil.slots :
                player.get_new_items_auto = False
            await ctx.send(f"You will now have to use `!new` command to check for new items received since the last time you checked.")

    @bot.command(name='todo')
    async def todo(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        bot.logger.info("todo command called")
        discord_profil = bot.bot_client.discord_db.get_discord_profile(ctx.author.id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        player = discord_profil.current_slot
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        elif player.todolist == [] :
            flavor = get_empty_todolist_flavor()
            await ctx.send(f"{player.player_name} : {flavor}")
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
            await ctx.send(msg)

        
    @bot.command(name="clearTodo")
    async def clear_todo(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        player = discord_profil.current_slot
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
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
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        player = discord_profil.current_slot
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
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        player = discord_profil.current_slot
        bot.logger.info(f"Wishlist command called for player {player.player_name}")
        wishlist = []
        for other_player in bot.bot_client.player_db.get_all_players() :
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
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        player = discord_profil.current_slot
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
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        player = discord_profil.current_slot
        await ctx.send(f"You have died {len(player.deaths)} times.")
    
    @bot.command(name='deathgraph')
    async def deathgraph(ctx) :
        if await bad_channel_check(ctx, bot):
            return
        discord_id = ctx.author.id
        discord_profil = bot.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        player = discord_profil.current_slot
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

            
            
    
