async def is_admin(ctx, bot):
    if str(ctx.author.id) in bot.admins:
        return True
    else:
        return False

def setup_admin_commands(bot) :
    
    @bot.command(name='admin', help='Admin command')
    async def admin_command(ctx):
        if not await is_admin(ctx, bot):
            return
        await ctx.send('This is an admin command.')
    
    @bot.command(name='computeChecks')
    async def compute_checks(ctx):
        if not await is_admin(ctx, bot):
            return
        await ctx.send("Computing checks for all players. This may take a while...")
        try :
            for player in bot.bot_client.player_db.get_all_players():
                bot.bot_client.compute_checks_for_player(player)
        except Exception as e:
            bot.logger.error(f"Error computing checks: {e}")
            await ctx.send(f"An error occurred while computing checks. Please try again later.")