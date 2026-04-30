from archipelago.hint_client import HintClient
from models.button import Button
from utils.colors import get_ansi_color_from_flag
from discord_bot.texts_flavors import *
import asyncio
import re
import matplotlib.pyplot as plt
from io import BytesIO
import discord

ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')

def strip_ansi(s):
    return ANSI_ESCAPE.sub('', s)

def ansi_ljust(s, width):
    return s + " " * (width - len(strip_ansi(s)))

async def bad_channel_check(ctx, bot) :
    if ctx.channel is not None and ctx.channel.id != bot.normal_channel_id :
        await ctx.send("""Cher Monsieur, Chère Madame, nous vous prions de bien vouloir apprendre à lire
Voilà quelque-chose, mon cher, que vous auriez pu faire,
Si vous aviez un peu de lettres et d’esprit
Mais d’esprit, ô le plus lamentable des êtres,
Vous n’en eûtes jamais un atome, et de lettres
Vous n’avez que les trois qui forment le mot : sot !
Eussiez-vous eu d’ailleurs la présence d’esprit qu’il faut,
Pour pouvoir là, devant ces deux pauvres channels discord,
vous servir du bon et susnommé « channel à bot »,
Que vous n’en eussiez pas tapé le quart
De la moitié du commencement de votre commande, 
Que nous vous la renvoyons, avec assez de verve,
Et ne permettons pas qu’une commande entacha ce chanel tout propre. 

Arthur et Tanguy""")
        return True
    return False

async def send_new_items(bot, player_id) :
    player = bot.bot_client.player_db.get_player_by_discord_id(player_id)
    user = await bot.bot_client.fetch_user(player_id)
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
            await ctx.send(msg)

        
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

    @bot.command(name='help')
    async def help(ctx, command: str = None) :
        if await bad_channel_check(ctx, bot):
            return
        if command is None :
            msg = """**Available commands:**\n
`!register <player_name>` : Register your discord account to a player. You will receive notifications about this player's items and you can use other commands to see the player's todo list and new items.\n
`!unregister <Optional : player_name>` : Unregister your discord account from a player. If player_name is not provided, it will unregister from the player you are currently registered to. If player_name is provided, it will unregister from that player if you are registered to it.\n
`!players` : List all players in the game.\n
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
                msg = """`!players` : List all players in the game.\n
Example : `!players` will list all players in the game. This command is useful to know the exact spelling of the player names to use them in other commands."""
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
            
            
    