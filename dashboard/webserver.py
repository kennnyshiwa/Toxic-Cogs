from aiohttp import web
import aiohttp
import asyncio

class WebServer:
    def __init__(self, bot, cog):
        self.app = web.Application()
        self.bot = bot
        self.port = 42356
        self.handler = None
        self.runner = None
        self.site = None
        self.div = ""
        self.body = None
        self.var = 0
        self.path = None
        self.cog = cog

    def __unload(self):
        self.bot.loop.create_task(self.runner.cleanup())

    async def home(self, request):
        #current_path = self.path / "templates/index.html"
        current_path = r"C:\Users\tmsb7\Envs\rewrite2\red-cogs-submit\wip-cogs\dashboard\templates\index.html"
        file = open(str(current_path), 'r')
        html = file.read()
        # html.replace("{cog_data_path}", str(self.path / "resources/text_launcher"))
        html = html.replace("{cog_data_path}", str(r"C:\Users\tmsb7\Envs\rewrite2\red-cogs-submit\wip-cogs\dashboard"))
        return web.Response(text=html, content_type="text/html")

    async def dashboard(self, request):
        #current_path = self.path / "templates/dashboard.html"
        current_path = r"C:\Users\tmsb7\Envs\rewrite2\red-cogs-submit\wip-cogs\dashboard\templates\dashboard.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")
    
    async def cogs(self, request):
        return aiohttp.web.HTTPFound('http://localhost:42356/dashboard')

    async def cogs_admin(self, request):
        current_path = r"C:\Users\tmsb7\Envs\rewrite2\red-cogs-submit\wip-cogs\dashboard\templates\cog_pages\admin.html"
        file = open(str(current_path), 'r')
        html = file.read()
        return web.Response(text=html, content_type="text/html")

    async def cogs_admin_load_filter(self, request):
        await self.cog.rpc_client.call('CORE__LOAD', {"cog_names": ["filter"], "kwargs": {}})
        return aiohttp.web.HTTPFound('http://localhost:42356/dashboard')

    async def make_webserver(self, path):
        self.path = path
        cog = self.bot.get_cog("Dashboard")
        await asyncio.sleep(3)
        self.app.router.add_get("/", self.home)
        self.app.router.add_get("/dashboard", self.dashboard)
        self.app.router.add_get("/cogs", self.cogs)
        self.app.router.add_get("/cogs/admin", self.cogs_admin)
        self.app.router.add_get("/cogs/admin/load/filter", self.cogs_admin_load_filter)
        #self.app.add_routes([web.static('/resources', self.path)])
        self.app.add_routes([web.static('/resources', r"C:\Users\tmsb7\Envs\rewrite2\red-cogs-submit\wip-cogs\dashboard")])
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.handler = self.app.make_handler(debug=True)
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await self.site.start()
        print("WebTest started ...")