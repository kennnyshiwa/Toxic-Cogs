async def get_cogs(bot):
    loaded = set(bot.extensions.keys())
    all_cogs = set(await bot.cog_mgr.available_modules())
    unloaded = all_cogs - loaded
    loaded = sorted(list(loaded), key=str.lower)
    unloaded = sorted(list(unloaded), key=str.lower)
    return loaded, unloaded