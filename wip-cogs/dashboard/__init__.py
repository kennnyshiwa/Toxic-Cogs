from .dashboard import Dashboard

async def setup(bot):
    cog = Dashboard(bot)
    #await cog.initialize()
    bot.add_cog(cog)