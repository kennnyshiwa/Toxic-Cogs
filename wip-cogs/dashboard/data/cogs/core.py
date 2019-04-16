from redbot.core import errors
from .exceptions import LoadedError, LocationError, LoadingError, NotLoadedError

async def load_cog(bot, cog):
    core = bot.get_cog("Core")
    try:
        spec = await bot.cog_mgr.find_cog(cog)
        if spec:
            pass
        else:
            raise LocationError("Could not locate cog")
    except Exception as e:
        raise LocationError("Issue when locating cog")

    try:
        core._cleanup_and_refresh_modules(spec.name)
        await bot.load_extension(spec)
    except errors.PackageAlreadyLoaded:
        raise LoadedError("Already loaded")
    except errors.CogLoadError as e:
        raise LoadingError(str(e))
    except Exception as e:
        raise LoadingError(str(e))
    else:
        await bot.add_loaded_package(cog)
        return True

async def unload_cog(bot, cog):
    if cog in bot.extensions:
        bot.unload_extension(cog)
        await bot.remove_loaded_package(cog)
    else:
        raise NotLoadedError("Cog isn't loaded.")
    return True