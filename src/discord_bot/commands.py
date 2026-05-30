from archipelago.hint_client import HintClient
from models.discord_profil import DiscordProfile
from models.button import Button
from utils.colors import get_ansi_color_from_flag
from utils.name_finder import resolve_player_name
from discord_bot.texts_flavors import *
import asyncio
import re
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import matplotlib.colors as mcolors
from io import BytesIO
import discord

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(s):
    return ANSI_ESCAPE.sub('', s)

def ansi_ljust(s, width):
    return s + " " * (width - len(strip_ansi(s)))

async def send_new_items(bot, session, player_id) :
    player = session.bot_client.player_db.get_player_by_discord_id(player_id)
    user = await bot.fetch_user(player_id)
    if user.dm_channel is None :
        await user.create_dm() 
    if player is None :
        session.bot_client.logger.error(f"Player with discord id {player_id} not found.")
        return
    elif len(player.new_items) == 0 :
        session.bot_client.logger.info(f"Player found : {player.player_name} but no new items to send.")
        # DM player if no new items, to avoid spamming the channel
        await user.dm_channel.send("You have not received any new items since the last time you checked.")
    else :
        session.bot_client.logger.info(f"Player found : {player.player_name} with {len(player.new_items)} new items to send.")
        msg = "```ansi\n"
        async with session.bot_client.lock:
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
        
async def check_world_channel(bot, channel_id) :
    session = bot.world_manager.get_world_from_channel(channel_id)
    if session is None :
        bot.custom_logger.warning(f"Received message from channel {channel_id} but no world is associated to this channel.")
        return None
    return session

def setup_commands(bot):
    
    @bot.command(name='hint')
    async def hint(ctx, *, hint: str):
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        bot.custom_logger.info(f"Hint command called with hint : {hint}")
        discord_profil = session.bot_client.discord_db.get_discord_profile(ctx.author.id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            return
        player = discord_profil.current_slot
        try :
            hint_client_instance = HintClient(player.player_name, 
                                            player.player_game, 
                                            hint, 
                                            session.bot_client,
                                            session.bot_client.config)
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
                    button = Button(item, session.bot_client)
                    message = await ctx.send(message, view=button)
                    button.message = message
                except :
                    await ctx.send(message)
            # Terminate hint client
            await hint_client_instance.stop()
        except Exception as e :
            session.bot_client.logger.error(f"Error sending hint: {e}")
            await ctx.send(f"An error occurred while sending the hint. Please try again later.")

    @bot.command(name='players')
    async def players(ctx):
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        players = session.bot_client.player_db.get_all_players_names()
        await ctx.send(f"Players in this multiworld are : {', '.join(players)}")

    @bot.command(name='register')
    async def register(ctx, *, player_name: str) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        # Check if player name is valid
        player_name = resolve_player_name(player_name, session.bot_client.player_db.get_all_players_names())
        if player_name is None :
            await ctx.send(f"Player name {player_name} not found. Please check the spelling and try again.\n\
Available player names are : {', '.join(session.bot_client.player_db.get_all_players_names())}")
        elif session.bot_client.player_db.get_player_by_name(player_name).discord_id is not None :
            player = session.bot_client.player_db.get_player_by_name(player_name)
            if player.discord_id == ctx.author.id :
                await ctx.send(f"You are already registered to player {player_name}.")
            else :
                await ctx.send(f"Player {player_name} is already registered by {player.discord_id}.\nIf you think this is an error, please contact the administrator.")
        else :
            discord_profil = session.bot_client.discord_db.get_discord_profile(ctx.author.id)
            if discord_profil is None :
                discord_profil = DiscordProfile(ctx.author.name, ctx.author.id)
            player = session.bot_client.player_db.get_player_by_name(player_name)
            # Link player and discord profile
            discord_profil.slots.append(player)
            discord_profil.current_slot = player
            session.bot_client.discord_db.add_discord_profile(discord_profil)
            session.bot_client.player_db.set_discord_id(player, discord_profil.id)
            await ctx.send(f"Player {player_name} successfully registered to discord user {ctx.author.name}#{ctx.author.discriminator}.\n\
You are currently registered to : {', '.join([p.player_name for p in discord_profil.slots])}")

    @bot.command(name='unregister')
    async def unregister(ctx, *, player_name: str = None) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
        registered_players = [p.player_name for p in discord_profil.slots] if discord_profil else []
        if registered_players == [] :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            return
        player_name = resolve_player_name(player_name, registered_players) if player_name else None
        if player_name is not None and player_name not in registered_players :
            await ctx.send(f"You are not registered to player {player_name}. You are currently registered to : {', '.join(registered_players)}.")
        elif player_name is not None and player_name in registered_players :
            player = session.bot_client.player_db.get_player_by_name(player_name)
            # Unlink player and discord profile
            discord_profil.slots.remove(player)
            session.bot_client.player_db.set_discord_id(player, None)
            await ctx.send(f"Player {player_name} successfully unregistered from discord user {ctx.author.name}#{ctx.author.discriminator}.")
        else :
            # Unregister from all players
            for player in discord_profil.slots:
                session.bot_client.player_db.set_discord_id(player, None)
            discord_profil.slots.clear()
            await ctx.send(f"All players successfully unregistered from discord user {ctx.author.name}#{ctx.author.discriminator}.")
            
    @bot.command(name='current')
    async def current(ctx) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None or discord_profil.slots == [] :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            return
        else :
            current_player = discord_profil.current_slot
            await ctx.send(f"You are currently tracking {current_player.player_name}. Use `!switch` command to switch to another player if you are registered to multiple players.")
    
    @bot.command(name='switch')
    async def switch(ctx, *, player_name: str = None) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")    
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
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
            player = session.bot_client.player_db.get_player_by_name(player_name)
            discord_profil.current_slot = player
            await ctx.send(f"Successfully switched to player {player_name}.")

    @bot.command(name='new')
    async def new(ctx, all: str = None) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None or discord_profil.slots == [] :
            await ctx.send(f"You are not registered to any player. Please register first using `!register <player_name>` command.")
            return
        elif all == "all" :
            for player in discord_profil.slots :
                await send_new_items(bot, session, player.discord_id)
        else :
            current_player = discord_profil.current_slot
            await send_new_items(bot, session, current_player.discord_id)
            
    @bot.command(name='enableping')
    async def enableping(ctx) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
        registered_players = [p.player_name for p in discord_profil.slots] if discord_profil else []
        if registered_players == [] :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            for player in discord_profil.slots :
                player.allow_ping = True
            await ctx.send(f"This discord bot will now ping you when another player finds an item relevant to your todo list.")
    
    @bot.command(name='disableping')
    async def disableping(ctx) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
        registered_players = [p.player_name for p in discord_profil.slots] if discord_profil else []
        if registered_players == [] :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            for player in discord_profil.slots :
                player.allow_ping = False
            await ctx.send(f"This discord bot won't bother you anymore with pings")
            
    @bot.command(name='enablenewitems')
    async def enablenewitems(ctx) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
        registered_players = [p.player_name for p in discord_profil.slots] if discord_profil else []
        if registered_players == [] :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            for player in discord_profil.slots :
                player.get_new_items_auto = True
            await ctx.send(f"You will now receive new items automatically in DM as soon as you start playing.")
            
    @bot.command(name='disablenewitems')
    async def disablenewitems(ctx) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
        registered_players = [p.player_name for p in discord_profil.slots] if discord_profil else []
        if registered_players == [] :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
        else :
            for player in discord_profil.slots :
                player.get_new_items_auto = False
            await ctx.send(f"You will now have to use `!new` command to check for new items received since the last time you checked.")

    @bot.command(name='todo')
    async def todo(ctx) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        bot.custom_logger.info("todo command called")
        discord_profil = session.bot_client.discord_db.get_discord_profile(ctx.author.id)
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
            bot.custom_logger.info(f"Player found : {player.player_name} with {len(player.todolist)} items in todo list.")
            async with session.bot_client.lock:
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
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        player = discord_profil.current_slot
        if player is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        else :
            async with session.bot_client.lock:
                player.todolist.clear()
            msg = get_clear_todolist_flavor()
            await ctx.send(msg)
            
    @bot.command(name='removeTodo')
    async def remove_todo(ctx, *, item_name: str) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        player = discord_profil.current_slot
        async with session.bot_client.lock:
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
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        player = discord_profil.current_slot
        session.bot_client.logger.info(f"Wishlist command called for player {player.player_name}")
        wishlist = []
        for other_player in session.bot_client.player_db.get_all_players() :
            async with session.bot_client.lock:
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
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
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
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
        if discord_profil is None :
            await ctx.send(f"You are not registered to any player. Please register first usign `!register <name>` command.")
            return
        player = discord_profil.current_slot
        await ctx.send(f"You have died {len(player.deaths)} times.")
    
    @bot.command(name='deathgraph')
    async def deathgraph(ctx) :
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        discord_id = ctx.author.id
        discord_profil = session.bot_client.discord_db.get_discord_profile(discord_id)
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
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        deaths_dict = {}
        for player in session.bot_client.player_db.get_all_players() :
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
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            await ctx.send("This channel is not associated to any world. Please use the commands in the correct channel or create a new world with !newWorld.")
            return
        percentage_dict = {}; checks_dict = {}
        for player in session.bot_client.player_db.get_all_players() :
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
        session = await check_world_channel(bot, ctx.channel.id)
        if session is None :
            msg = (
                "**Available commands**\n\n"
                "`!newWorld` - Create and initialize a new Archipelago multiworld.\n"
                "This command can be used in any channel and allows you to set up a new multiworld session with interactive configuration or by uploading a `config.json` file.\n\n"
                "`!delete_world` - Delete the multiworld associated with the current channel.\n"
                "This command stops the bot from tracking the multiworld in this channel and removes all related data, but does not affect the actual Archipelago session.\n"
                "If admins are configured in the world, only admins can use this command."
            )
            await ctx.send(msg)
            return

        commands_help = {
            "register": {
                "usage": "`!register <player_name>`",
                "description": "Link your Discord account to a player.",
                "details": (
                    "You will receive notifications about this player's items and gain access "
                    "to player-specific commands.\n\n"
                    "Example:\n"
                    "`!register Alice`"
                )
            },
            "unregister": {
                "usage": "`!unregister [player_name]`",
                "description": "Unlink your account from one or more players.",
                "details": (
                    "If no player is specified, you will be unregistered from all registered players.\n\n"
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
            "current": {
                "usage": "`!current`",
                "description": "Display your currently tracked player.",
                "details": (
                    "This player is used by commands such as "
                    "`!todo`, `!wishlist`, `!hint`, and `!new`."
                )
            },
            "switch": {
                "usage": "`!switch [player_name]`",
                "description": "Change your tracked player.",
                "details": (
                    "Without arguments, switches to the next registered player.\n"
                    "With a player name, directly switches to that player.\n\n"
                    "Examples:\n"
                    "`!switch`\n"
                    "`!switch Alice`"
                )
            },
            "hint": {
                "usage": "`!hint <text>`",
                "description": "Send a hint request to the tracker.",
                "details": (
                    "Recognized hints may provide interactions such as "
                    "adding items to your todo list.\n\n"
                    "Example:\n"
                    "`!hint City Crest`"
                )
            },
            "new": {
                "usage": "`!new`",
                "description": "Check newly received items.",
                "details": (
                    "Displays items received since your last check. "
                    "Results are sent through DM."
                )
            },
            "todo": {
                "usage": "`!todo`",
                "description": "Display your todo list.",
                "details": (
                    "Shows the items currently tracked for your active player."
                )
            },
            "cleartodo": {
                "usage": "`!clearTodo`",
                "description": "Clear your todo list.",
                "details": "Removes every item from your current todo list."
            },
            "removetodo": {
                "usage": "`!removeTodo <item_name>`",
                "description": "Remove an item from your todo list.",
                "details": (
                    "Example:\n"
                    "`!removeTodo Hookshot`"
                )
            },
            "wishlist": {
                "usage": "`!wishlist`",
                "description": "Display items other players marked for you.",
                "details": (
                    "Shows all wishlist items targeting your currently tracked player."
                )
            },
            "enableping": {
                "usage": "`!enableping`",
                "description": "Enable todo notifications.",
                "details": (
                    "You will be pinged when another player finds an item "
                    "present in your todo list."
                )
            },
            "disableping": {
                "usage": "`!disableping`",
                "description": "Disable todo notifications.",
                "details": "Stops ping notifications from the bot."
            },
            "enablenewitems": {
                "usage": "`!enablenewitems`",
                "description": "Enable automatic new item notifications.",
                "details": (
                    "You will automatically receive newly collected items "
                    "via DM when connecting to the game."
                )
            },
            "disablenewitems": {
                "usage": "`!disablenewitems`",
                "description": "Disable automatic new item notifications.",
                "details": (
                    "You will need to use `!new` manually to check received items."
                )
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
                "description": "Generate a death progression graph.",
                "details": "Displays cumulative deaths over time."
            },
            "globaldeaths": {
                "usage": "`!globaldeaths`",
                "description": "Compare deaths between all players.",
                "details": "Generates a comparative graph for every player."
            },
            "progressgraph": {
                "usage": "`!progressGraph`",
                "description": "Generate a progression graph.",
                "details": (
                    "Displays progression information for all players "
                    "(checks found, completion percentage, etc.)."
                )
            },
            "help": {
                "usage": "`!help [command]`",
                "description": "Display help information.",
                "details": (
                    "Use without arguments to list all commands or specify "
                    "a command for detailed help."
                )
            }
        }

        if command is None:
            msg = (
                "**Available commands**\n\n"

                "**Player management**\n"
                "`!register <player>`\n"
                "`!unregister [player]`\n"
                "`!players`\n"
                "`!current`\n"
                "`!switch [player]`\n\n"

                "**Hints & progression**\n"
                "`!hint <text>`\n"
                "`!todo`\n"
                "`!clearTodo`\n"
                "`!removeTodo <item>`\n"
                "`!wishlist`\n"
                "`!new`\n\n"

                "**Statistics**\n"
                "`!wastedOnArchipelago`\n"
                "`!deaths`\n"
                "`!deathgraph`\n"
                "`!globaldeaths`\n"
                "`!progressGraph`\n\n"

                "**Notifications**\n"
                "`!enableping`\n"
                "`!disableping`\n"
                "`!enablenewitems`\n"
                "`!disablenewitems`\n\n"

                "Use `!help <command>` for detailed information about a specific command."
            )
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

            
            
    
