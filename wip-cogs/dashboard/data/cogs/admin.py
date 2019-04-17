from .exceptions import NotLoadedError
from redbot.cogs.admin.announcer import Announcer

# Fake context for announcing

class FakeContextAnnouncer:
    def __init__(self, bot):
        self.bot = bot

async def announce(bot, message):
    cog = bot.get_cog("Admin")
    if not cog:
        raise NotLoadedError("Admin cog must be loaded.")
    if not cog.is_announcing():
        announcer = Announcer(FakeContextAnnouncer(bot), message, config=cog.conf)
        announcer.start()
        cog.__current_announcer = announcer
        return True
    else:
        return False