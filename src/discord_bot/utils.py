import re
from discord_bot.texts_flavors import get_todolist_flavor
from utils.colors import get_ansi_color_from_flag

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
        
def build_todo_message(items):

    flavor = get_todolist_flavor()

    msg = f"```ansi\n{flavor}\n\n"

    l1 = max(max(len(item.player_recieving.player_name) for item in items), len("For")) + 1
    l2 = max(max(len(item.item_name) for item in items), len("Item")) + 1
    l3 = max(max(len(item.location_name) for item in items), len("Location")) + 1

    msg += f"{'Status'.ljust(8)} || {'For'.ljust(l1)} || {'Item'.ljust(l2)} || {'Location'.ljust(l3)}\n"

    for item in items:

        status = (
            "\u001b[0;32m✅\u001b[0m"
            if item.doable
            else "\u001b[0;31m❌\u001b[0m"
        )

        msg += (
            f"{status.ljust(13)} || "
            f"{ansi_ljust(item.player_recieving.name_colored, l1)} || "
            f"{item.item_name.ljust(l2)} || "
            f"{item.location_name.ljust(l3)}\n"
        )

    msg += "```"

    return msg