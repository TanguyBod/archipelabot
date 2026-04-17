def setup_events(bot):

    async def discord_sender(channel, queue):
        while True:
            msg = await queue.get()
            await channel.send(msg)

    @bot.event
    async def on_ready():
        channel = bot.get_channel(bot.normal_channel_id)

        bot.loop.create_task(
            discord_sender(channel, bot.messages_to_send)
        )