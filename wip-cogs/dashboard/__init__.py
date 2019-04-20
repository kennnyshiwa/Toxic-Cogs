from .dashboard import Dashboard

async def setup(bot):
    cog = Dashboard(bot)
    if (await cog.conf.password()) == "youshallnotpass":
        owner = await bot.get_user_info(bot.owner_id)
        try:
            await owner.send("You haven't configured the password to the dashboard yet!  It is recommended to do so in case other users can access it!")
        except:
            # Welp, I tried.  Their fault they didnt change it if it gets hacked
            pass
    bot.add_cog(cog)