from .dashboard import Dashboard
from redbot.core import __version__


async def setup(bot):
    cog = Dashboard(bot)
    if not __version__ in cog.__red__:
        try:
            owner = await bot.get_user_info(bot.owner_id)
        except AttributeError:
            owner = await bot.fetch_user(bot.owner_id)
        await owner.send(
            f"Warning!  You are using a version of Dashboard that has not been tested on your version!  You may encounter errors when using it.  Please report issues to Neuro Assassin#4779 <@473541068378341376> in the Cog Server.\n\n**Current Red Version: {__version__}\nDashboard Red Version: {cog.__red__}**"
        )
    bot.add_cog(cog)
