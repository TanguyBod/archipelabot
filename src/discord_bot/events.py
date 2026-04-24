from discord_bot.commands import send_new_items

def setup_events(bot):

    async def discord_sender(channel, queue):
        while True:
            msg = await queue.get()
            await channel.send(msg)
            
    async def dm_sender(queue) :
        while True:
            player, msg = await queue.get()
            if player.discord_id :
                if msg == "new_items" :
                    await send_new_items(bot, player.discord_id)
            else :
                bot.logger.warning(f"Player {player.player_name} does not have a valid Discord ID or DMs are disabled, cannot send DM")    

    @bot.event
    async def on_ready():
        channel_normal = bot.get_channel(bot.normal_channel_id)
        channel_ping = bot.get_channel(bot.ping_channel_id)
        
        bot.loop.create_task(
            discord_sender(channel_normal, bot.messages_to_send)
        )
        bot.loop.create_task(
            discord_sender(channel_ping, bot.ping_queue)
        )
        bot.loop.create_task(
            dm_sender(bot.dm_queue)
        )
        