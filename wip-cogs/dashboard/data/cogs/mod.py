from .exceptions import InvalidModel, NotLoadedError, HackedError


async def ignore(bot, mtype, specifier, identifier):
    cog = bot.get_cog("Mod")
    if not cog:
        raise NotLoadedError("Mod cog must be loaded")
    if mtype == "channel":
        if specifier == "id":
            channel = bot.get_channel(int(identifier))
        elif specifier == "name":
            channel = None
            for c in bot.get_all_channels():
                if c.name == identifier:
                    channel = c
        else:
            raise HackedError("You hacked the options")
        if not channel:
            raise InvalidModel(
                f"{mtype} with the identifier {identifier} did not find any {mtype}s with the same {specifier}"
            )
        if not await cog.settings.channel(channel).ignored():
            await cog.settings.channel(channel).ignored.set(True)
            return True
        else:
            return False
    elif mtype == "guild":
        if specifier == "id":
            guild = bot.get_guild(int(identifier))
        elif specifier == "name":
            guild = None
            for g in bot.guilds:
                if g.name == identifier:
                    guild = g
        else:
            raise HackedError("You hacked the options")
        if not guild:
            raise InvalidModel(
                f"{mtype} with the identifier {identifier} did not find any {mtype}s with the same {specifier}"
            )
        if not await cog.settings.guild(guild).ignored():
            await cog.settings.guild(guild).ignored.set(True)
            return True
        else:
            return False
    else:
        raise HackedError("You hacked the options")


async def unignore(bot, mtype, specifier, identifier):
    cog = bot.get_cog("Mod")
    if not cog:
        raise NotLoadedError("Mod cog must be loaded")
    if mtype == "channel":
        if specifier == "id":
            channel = bot.get_channel(int(identifier))
        elif specifier == "name":
            channel = None
            for c in bot.get_all_channels():
                if c.name == identifier:
                    channel = c
        else:
            raise HackedError("You hacked the options")
        if not channel:
            raise InvalidModel(
                f"{mtype} with the identifier {identifier} did not find any {mtype}s with the same {specifier}"
            )
        if await cog.settings.channel(channel).ignored():
            await cog.settings.channel(channel).ignored.set(False)
            return True
        else:
            return False
    elif mtype == "guild":
        if specifier == "id":
            guild = bot.get_guild(int(identifier))
        elif specifier == "name":
            guild = None
            for g in bot.guilds:
                if g.name == identifier:
                    guild = g
        else:
            raise HackedError("You hacked the options")
        if not guild:
            raise InvalidModel(
                f"{mtype} with the identifier {identifier} did not find any {mtype}s with the same {specifier}"
            )
        if await cog.settings.guild(guild).ignored():
            await cog.settings.guild(guild).ignored.set(False)
            return True
        else:
            return False
    else:
        raise HackedError("You hacked the options")
