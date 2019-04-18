from aiohttp import web
import aiohttp
import asyncio
import random

from .data.cogs.mod import ignore
from .data.cogs.core import load_cog, unload_cog
from .data.cogs.admin import announce, serverlock
from .data.cogs.cogmanager import get_cogs, get_paths, add_path

from .data.cogs.exceptions import LoadedError, LocationError, LoadingError, NotLoadedError, HackedError, InvalidModel

memes = {
    "404": ["http://www.quickmeme.com/img/13/139e1e24e4563e65a4684885c035192402ae72fb05b5e42ad84509ef2137e212.jpg", "https://i.imgflip.com/11fjj7.jpg", "https://i.imgflip.com/gegi9.jpg", "http://www.quickmeme.com/img/84/84971a2e41c1d0ab5d45d1118f49e1f847f11f2d144f58873b4b6794e9164f5f.jpg", "https://i.pinimg.com/originals/84/03/d1/8403d12561c6ab7fd0bba3d9ecf9690f.jpg", "https://i.chzbgr.com/full/3745326080/h802C29B4/"]
}

class WebServer:
    def __init__(self, bot, cog):
        self.app = web.Application(middlewares=[self.error_middleware])
        self.bot = bot
        self.port = 42356
        self.handler = None
        self.runner = None
        self.site = None
        self.body = None
        self.path = None
        self.cog = cog
        self.session = aiohttp.ClientSession()

    def unload(self):
        self.bot.loop.create_task(self.runner.cleanup())
        self.session.detach()

    async def home(self, request):
        current_path = self.path / "templates/index.html"
        file = open(str(current_path), 'r')
        html = file.read()
        html = html.replace("{cog_data_path}", str(r"C:\Users\tmsb7\Envs\rewrite2\red-cogs-submit\wip-cogs\dashboard"))
        return web.Response(text=html, content_type="text/html")

    async def dashboard(self, request):
        current_path = self.path / "templates/dashboard.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")
    
    async def cogs(self, request):
        return aiohttp.web.HTTPFound('http://localhost:42356/dashboard')

    async def cogs_core_unload_action(self, request):
        if request.method != "POST":
            data = {
                "code": 405,
                "message": "Invalid method"
            }
            return web.json_response(data, status=data["code"], reason=data["message"])
        cog = await request.json()
        cog = cog['cog']
        try:
            success = await unload_cog(self.bot, cog)
        except NotLoadedError:
            data = {
                "code": 400,
                "message": "That cog is not loaded."
            }
        else:
            if success:
                data = {
                    "code": 200,
                    "message": "Unloaded"
                }
            else:
                data = {
                    "code": 500,
                    "message": "No error encountered, but no validation."
                }
        return web.json_response(data, status=data["code"], reason=data["message"])

    async def cogs_core_load_action(self, request):
        if request.method != "POST":
            data = {
                "code": 405,
                "message": "Invalid method"
            }
            return web.json_response(data, status=data["code"], reason=data["message"])
        cog = await request.json()
        cog = cog['cog']
        try:
            success = await load_cog(self.bot, cog)
        except LocationError as e:
            data = {
                "code": 400,
                "message": str(e)
            }
        except LoadedError as e:
            data = {
                "code": 409,
                "message": str(e)
            }
        except LoadingError as e:
            data = {
                "code": 500,
                "message": str(e)
            }
        else:
            if success:
                data = {
                    "code": 200,
                    "message": "Loaded"
                }
            else:
                data = {
                    "code": 500,
                    "message": "No error encountered, but no validation."
                }
        return web.json_response(data, status=data["code"], reason=data["message"])

    async def cogs_core_load(self, request):
        current_path = self.path / "templates/cog_pages/core/load.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_core_unload(self, request):
        current_path = self.path / "templates/cog_pages/core/unload.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_core_reload(self, request):
        current_path = self.path / "templates/cog_pages/core/reload.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_core(self, request):
        current_path = self.path / "templates/cog_pages/core.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_cogmanager_cogs_action(self, request):
        loaded, unloaded = await get_cogs(self.bot)
        data = {
            "l": loaded,
            "u": unloaded
        }
        return web.json_response(data)

    async def cogs_cogmanager_cogs(self, request):
        current_path = self.path / "templates/cog_pages/cogmanager/cogs.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_cogmanager_paths_action(self, request):
        install, core, cogs = await get_paths(self.bot)
        data = {
            "i": install,
            "core": core,
            "cogs": cogs
        }
        return web.json_response(data)

    async def cogs_cogmanager_paths(self, request):
        current_path = self.path / "templates/cog_pages/cogmanager/paths.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_cogmanager_add_path_action(self, request):
        path = await request.json()
        path = path['path']
        try:
            await add_path(self.bot, path)
        except ValueError:
            data = {
                "code": 400
            }
        else:
            data = {
                "code": 200
            }
        return web.json_response(data)

    async def cogs_cogmanager_add_path(self, request):
        current_path = self.path / "templates/cog_pages/cogmanager/add_path.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_cogmanager(self, request):
        current_path = self.path / "templates/cog_pages/cogmanager.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_admin_announce_action(self, request):
        message = await request.json()
        message = message["m"]
        try:
            success = await announce(self.bot, message)
        except NotLoadedError:
            data = {
                "success": False,
                "loaded": False
            }
        else:
            if success:
                data = {
                    "success": True
                }
            else:
                data = {
                    "success": False,
                    "loaded": True
                }
        return web.json_response(data)

    async def cogs_admin_announce(self, request):
        current_path = self.path / "templates/cog_pages/admin/announce.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_admin_serverlock_action(self, request):
        try:
            locked = await serverlock(self.bot)
        except NotLoadedError:
            data = {
                "success": False,
                "loaded": False,
                "locked": False
            }
        except:
            data = {
                "success": False,
                "loaded": True,
                "locked": False
            }
        else:
            if locked:
                data = {
                    "success": True,
                    "locked": True,
                    "loaded": True
                }
            else:
                data = {
                    "success": True,
                    "locked": False,
                    "loaded": True
                }
        return web.json_response(data)

    async def cogs_admin_serverlock(self, request):
        current_path = self.path / "templates/cog_pages/admin/serverlock.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_admin(self, request):
        current_path = self.path / "templates/cog_pages/admin.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_mod_ignore_action(self, request):
        data = await request.json()
        mtype = data["type"]
        specifier = data["sp"]
        identifier = data["thing"]
        try:
            ignored = await ignore(self.bot, mtype, specifier, identifier)
        except Exception as e:
            data = {
                "message": str(e)
            }
        else:
            if ignored:
                data = {
                    "message": "Now ignored."
                }
            else:
                data = {
                    "message": f"This {mtype} was already ignored."
                }
        return web.json_response(data)

    async def cogs_mod_ignore(self, request):
        current_path = self.path / "templates/cog_pages/mod/ignore.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_mod(self, request):
        current_path = self.path / "templates/cog_pages/mod.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def _credits(self, request):
        current_path = self.path / "templates/credits.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    @web.middleware
    async def error_middleware(self, request, handler):
        try:
            response = await handler(request)
            if response.status != 404:
                return response
            message = response.message
        except web.HTTPException as ex:
            if ex.status != 404:
                raise
            message = ex.reason
        current_path = self.path / "templates/404.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def make_webserver(self, path):
        self.path = path
        await asyncio.sleep(3)
        self.app.router.add_get("/", self.home)
        # Main pages
        self.app.router.add_get("/dashboard", self.dashboard)
        self.app.router.add_get("/credits", self._credits)
        self.app.router.add_get("/cogs", self.cogs)

        # Mod
        self.app.router.add_get("/cogs/mod", self.cogs_mod)
        self.app.router.add_get("/cogs/mod/ignore", self.cogs_mod_ignore)
        self.app.router.add_post("/cogs/mod/ignore/action", self.cogs_mod_ignore_action)

        # Core
        self.app.router.add_get("/cogs/core", self.cogs_core)
        self.app.router.add_get("/cogs/core/load", self.cogs_core_load)
        self.app.router.add_post("/cogs/core/load/action", self.cogs_core_load_action)
        self.app.router.add_get("/cogs/core/unload", self.cogs_core_unload)
        self.app.router.add_post("/cogs/core/unload/action", self.cogs_core_unload_action)
        self.app.router.add_get("/cogs/core/reload", self.cogs_core_reload)

        # Admin
        self.app.router.add_get("/cogs/admin", self.cogs_admin)
        self.app.router.add_get("/cogs/admin/announce", self.cogs_admin_announce)
        self.app.router.add_post("/cogs/admin/announce/action", self.cogs_admin_announce_action)
        self.app.router.add_get("/cogs/admin/serverlock", self.cogs_admin_serverlock)
        self.app.router.add_post("/cogs/admin/serverlock/action", self.cogs_admin_serverlock_action)

        # Cog Manager
        self.app.router.add_get("/cogs/cogmanager", self.cogs_cogmanager)
        self.app.router.add_get("/cogs/cogmanager/cogs", self.cogs_cogmanager_cogs)
        self.app.router.add_get("/cogs/cogmanager/cogs/action", self.cogs_cogmanager_cogs_action)
        self.app.router.add_get("/cogs/cogmanager/paths", self.cogs_cogmanager_paths)
        self.app.router.add_get("/cogs/cogmanager/paths/action", self.cogs_cogmanager_paths_action)
        self.app.router.add_get("/cogs/cogmanager/addpath", self.cogs_cogmanager_add_path)
        self.app.router.add_post("/cogs/cogmanager/addpath/action", self.cogs_cogmanager_add_path_action)


        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.handler = self.app.make_handler(debug=True)
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await self.site.start()
        print("Dashboard up!")