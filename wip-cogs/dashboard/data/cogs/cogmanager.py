async def get_cogs(bot):
    loaded = set(bot.extensions.keys())
    all_cogs = set(await bot.cog_mgr.available_modules())
    unloaded = all_cogs - loaded
    loaded = sorted(list(loaded), key=str.lower)
    unloaded = sorted(list(unloaded), key=str.lower)
    return loaded, unloaded


async def get_paths(bot):
    install = await bot.cog_mgr.install_path()
    core_path = bot.cog_mgr.CORE_PATH
    cog_paths = await bot.cog_mgr.user_defined_paths()
    return str(install), str(core_path), list(map(str, cog_paths))


async def add_path(bot, path):
    await bot.cog_mgr.add_path(path)
