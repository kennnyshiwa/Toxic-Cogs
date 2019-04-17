from aiohttp import web
import aiohttp
import asyncio

from .data.cogs.core import load_cog, unload_cog
from .data.cogs.cogmanager import get_cogs

from .data.cogs.exceptions import LoadedError, LocationError, LoadingError, NotLoadedError

class WebServer:
    def __init__(self, bot, cog):
        self.app = web.Application()
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

    async def cogs_admin(self, request):
        current_path = self.path / "templates/cog_pages/admin.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

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

    async def cogs_cogmanager(self, request):
        current_path = self.path / "templates/cog_pages/cogmanager.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def make_webserver(self, path):
        self.path = path
        await asyncio.sleep(3)
        self.app.router.add_get("/", self.home)
        self.app.router.add_get("/dashboard", self.dashboard)
        self.app.router.add_get("/cogs", self.cogs)
        self.app.router.add_get("/cogs/core", self.cogs_core)
        self.app.router.add_get("/cogs/admin", self.cogs_admin)
        self.app.router.add_get("/cogs/cogmanager", self.cogs_cogmanager)
        self.app.router.add_get("/cogs/cogmanager/cogs", self.cogs_cogmanager_cogs)
        self.app.router.add_get("/cogs/cogmanager/cogs/action", self.cogs_cogmanager_cogs_action)
        self.app.router.add_get("/cogs/core/load", self.cogs_core_load)
        self.app.router.add_post("/cogs/core/load/action", self.cogs_core_load_action)
        self.app.router.add_get("/cogs/core/unload", self.cogs_core_unload)
        self.app.router.add_post("/cogs/core/unload/action", self.cogs_core_unload_action)
        self.app.router.add_get("/cogs/core/reload", self.cogs_core_reload)
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.handler = self.app.make_handler(debug=True)
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await self.site.start()
        print("Dashboard up!")