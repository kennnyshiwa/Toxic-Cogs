from aiohttp import web
import aiohttp_jinja2
import jinja2
import time
import aiohttp
import asyncio
import random
import base64
import discord
import urllib
import json
from cryptography import fernet
from aiohttp_session import setup, get_session, session_middleware
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from .data.cogs.mod import ignore, unignore
from .data.cogs.core import load_cog, unload_cog
from .data.cogs.admin import announce, serverlock
from .data.cogs.cogmanager import get_cogs, get_paths, add_path

from .data.cogs.exceptions import LoadedError, LocationError, LoadingError, NotLoadedError, HackedError, InvalidModel

def not_login_required(fn):
    async def wrapped(cls, request, *args, **kwargs):
        app = request.app
        router = app.router
        session = await get_session(request)
        if 'user_id' in session:
            return web.HTTPFound("/dashboard")
        return await fn(cls, request, *args, **kwargs)
    return wrapped

def login_required(fn):
    async def wrapped(cls, request, *args, **kwargs):
        app = request.app
        router = app.router
        session = await get_session(request)
        if 'user_id' not in session:
            return web.HTTPFound("/login")
        return await fn(cls, request, *args, **kwargs)
    return wrapped

"""
Permissions are given via integer number, and their highest one across all mutual guilds.
For example, if they are admin in one, but a normal user in another, they still count as an admin

1 => Normal User
2 => Mod
3 => Administrator
4 => Guild Owner
5 => Bot Owner

1_ => Error pass
"""

async def get_permissions(cls, request):
    session = await get_session(request)
    user_id = int(session["user_id"])
    if await cls.bot.is_owner(await cls.bot.get_user_info(user_id)):
        return await cls.cog.conf.owner_perm()
    perm = 0
    if str(user_id) in (await cls.cog.conf.errorpass()):
        perm += 10
    # Check if guild owner
    for guild in cls.bot.guilds:
        if guild.owner_id == user_id:
            # They have guild owner, and since they aren't bot owner, its the highest they can have
            perm += 4
            return perm

    # Check if admin
    for guild in cls.bot.guilds:
        member = guild.get_member(user_id)
        if not member:
            continue
        if member.guild_permissions.administrator:
            perm += 3
            return perm

    # Check if mod
    for guild in cls.bot.guilds:
        member = guild.get_member(user_id)
        role = await cls.bot.db.guild(guild).mod_role()
        if role in [mrole.id for mrole in member.roles]:
            perm += 2
            return perm

    return perm + 1

"""
Basically the same as the above, but uses a specific guild/channel and checks permissions
Follows the same integers as above
"""
async def get_specific_perms(cls, request, mobject):
    session = await get_session(request)
    user_id = int(session["user_id"])
    if await cls.bot.is_owner(await cls.bot.get_user_info(user_id)):
        return await cls.cog.conf.owner_perm()
    mobject = int(mobject)
    thing = cls.bot.get_guild(mobject)
    if not thing:
        thing = cls.bot.get_channel(mobject)
        if not thing:
            return 0
    if isinstance(thing, discord.Guild):
        member = thing.get_member(user_id)
        if not member:
            return 0
        if thing.owner_id == user_id:
            return 4
        if member.guild_permissions.administrator:
            return 3
        role = await cls.bot.db.guild(thing).mod_role()
        if role in [mrole.id for mrole in member.roles]:
            return 2
        return 1
    else:
        member = thing.guild.get_member(user_id)
        if not member:
            return 0
        if thing.guild.owner_id == user_id:
            return 4
        if thing.permissions_for(member).administrator:
            return 3
        role = await cls.bot.db.guild(thing.guild).mod_role()
        if role in [mrole.id for mrole in member.roles]:
            return 2
        return 1
        

class WebServer:
    def __init__(self, bot, cog):
        fernet_key = fernet.Fernet.generate_key()
        secret_key = base64.urlsafe_b64decode(fernet_key)
        self.app = web.Application(middlewares=[self.error_middleware, session_middleware(EncryptedCookieStorage(secret_key))])
        self.bot = bot
        self.port = 42356
        self.handler = None
        self.runner = None
        self.site = None
        self.path = None
        self.cog = cog
        self.session = aiohttp.ClientSession()

    def unload(self):
        self.bot.loop.create_task(self.runner.cleanup())
        self.session.detach()

    def get_context(self, cog):
        with open(str(self.path / "cogs/cards.json"), "r") as read_file:
            data = json.load(read_file)
        return data[cog]


    @not_login_required
    async def login_action(self, request):
        session = await get_session(request)
        password = await self.cog.conf.password()
        given = (await request.json())["pass"]
        if given == password:
            session["password"] = password
            return web.json_response({"response": "Logged in"})
        else:
            return web.json_response({"response": "Failed to log in"})

    @not_login_required
    async def login(self, request):
        response = aiohttp_jinja2.render_template("login.html", request, {"redirect": urllib.parse.quote((await self.cog.conf.redirect())), "id": str(self.bot.user.id)})
        return response

    async def home(self, request):
        response = aiohttp_jinja2.render_template("index.html", request, {})
        return response

    @not_login_required
    async def use_code(self, request):
        try:
            code = request.query["code"]
        except KeyError:
            return web.json_response(str(request.query))
        redirect = await self.cog.conf.redirect()
        data = {
            "client_id": self.bot.user.id,
            "client_secret": (await self.cog.conf.secret()),
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect,
            "scope": "identify"
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = await self.session.post("https://discordapp.com/api/v6/oauth2/token", data=data, headers=headers)
        try:
            token = (await response.json())["access_token"]
        except KeyError:
            return web.json_response(await response.json())
        new = await self.session.get("https://discordapp.com/api/v6/users/@me", headers={"Authorization": f"Bearer {token}"})
        new_data = await new.json()
        if "id" in new_data:
            session = await get_session(request)
            session["user_id"] = new_data["id"]
            return aiohttp.web.HTTPFound('/dashboard')
        return web.json_response(await new.json())

    @login_required
    async def dashboard(self, request):
        response = aiohttp_jinja2.render_template("dashboard.html", request, {})
        return response

    @login_required
    async def error_remove_action(self, request):
        _id = int((await request.json())["id"])
        data = await get_permissions(self, request)
        if data < 10:
            return aiohttp.web.HTTPFound('/dashboard')
        removed = False
        async with self.cog.conf.command_errors() as c:
            for e in c:
                if e["id"] == _id:
                    c.remove(e)
                    removed = True
        if removed:
            return web.json_response({"status": 200})
        return web.json_response({"status": 400})

    @login_required
    async def error_view_action(self, request):
        _id = int((await request.json())["id"])
        data = await get_permissions(self, request)
        if data < 10:
            return aiohttp.web.HTTPFound('/dashboard')
        selection = None
        async with self.cog.conf.command_errors() as c:
            for e in c:
                if e["id"] == _id:
                    selection = e
        if selection:
            data = {
                "success": True,
                "id": _id,
                "invoker": selection["invoker"],
                "command": selection["command"],
                "long": selection["error"],
                "short": selection["short"]
            }
        else:
            data = {
                "success": False
            }
        return web.json_response(data)        

    @login_required
    async def error_view(self, request):
        data = await get_permissions(self, request)
        if data < 10:
            return aiohttp.web.HTTPFound('/dashboard')
        response = aiohttp_jinja2.render_template("error_view.html", request, {})
        return response

    @login_required
    async def monitor_time(self, request):
        t = time.time()
        data = await get_permissions(self, request)
        e = time.time()
        returning = {
            "perm": data,
            "time": e - t
        }
        return web.json_response(returning)

    @login_required
    async def errors_action(self, request):
        data = await get_permissions(self, request)
        if data < 10:
            return aiohttp.web.HTTPFound('/dashboard')
        c = await self.cog.conf.command_errors()
        return web.json_response({"data": c})

    @login_required
    async def errors(self, request):
        data = await get_permissions(self, request)
        if data < 10:
            return aiohttp.web.HTTPFound('/dashboard')
        response = aiohttp_jinja2.render_template("errors.html", request, {})
        return response
    
    @login_required
    async def cogs(self, request):
        return aiohttp.web.HTTPFound('/dashboard')

    @login_required
    async def cogs_core_unload_action(self, request):
        data = await get_permissions(self, request)
        if data > 10:
            data -= 10
        if data < 5:
            return web.json_response(status=403)
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

    @login_required
    async def cogs_core_load_action(self, request):
        data = await get_permissions(self, request)
        if data > 10:
            data -= 10
        if data < 5:
            return web.json_response(status=403)
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

    @login_required
    async def cogs_core_load(self, request):
        data = await get_permissions(self, request)
        allowed = True
        if data > 10:
            data -= 10
        if data < 5:
            allowed = False
        response = aiohttp_jinja2.render_template("cog_pages/core/load.html", request, {"can": allowed})
        return response

    @login_required
    async def cogs_core_unload(self, request):
        data = await get_permissions(self, request)
        allowed = True
        if data > 10:
            data -= 10
        if data < 5:
            allowed = False
        response = aiohttp_jinja2.render_template("cog_pages/core/unload.html", request, {"can": allowed})
        return response

    @login_required
    async def cogs_core_reload(self, request):
        data = await get_permissions(self, request)
        allowed = True
        if data > 10:
            data -= 10
        if data < 5:
            allowed = False
        response = aiohttp_jinja2.render_template("cog_pages/core/reload.html", request, {"can": allowed})
        return response

    @login_required
    async def cogs_core(self, request):
        context = self.get_context("core")
        response = aiohttp_jinja2.render_template("cog_pages/core.html", request, context)
        return response

    @login_required
    async def cogs_cogmanager_cogs_action(self, request):
        data = await get_permissions(self, request)
        if data > 10:
            data -= 10
        if data < 5:
            return web.json_response(status=403)
        loaded, unloaded = await get_cogs(self.bot)
        data = {
            "l": loaded,
            "u": unloaded
        }
        return web.json_response(data)

    @login_required
    async def cogs_cogmanager_cogs(self, request):
        data = await get_permissions(self, request)
        allowed = True
        if data > 10:
            data -= 10
        if data < 5:
            allowed = False
        response = aiohttp_jinja2.render_template("cog_pages/cogmanager/cogs.html", request, {"can": allowed})
        return response

    @login_required
    async def cogs_cogmanager_paths_action(self, request):
        data = await get_permissions(self, request)
        if data > 10:
            data -= 10
        if data < 5:
            return web.json_response(status=403)
        install, core, cogs = await get_paths(self.bot)
        data = {
            "i": install,
            "core": core,
            "cogs": cogs
        }
        return web.json_response(data)

    @login_required
    async def cogs_cogmanager_paths(self, request):
        data = await get_permissions(self, request)
        allowed = True
        if data > 10:
            data -= 10
        if data < 5:
            allowed = False
        response = aiohttp_jinja2.render_template("cog_pages/cogmanager/paths.html", request, {"can": allowed})
        return response

    @login_required
    async def cogs_cogmanager_add_path_action(self, request):
        data = await get_permissions(self, request)
        if data > 10:
            data -= 10
        if data < 5:
            return web.json_response(status=403)
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

    @login_required
    async def cogs_cogmanager_add_path(self, request):
        data = await get_permissions(self, request)
        allowed = True
        if data > 10:
            data -= 10
        if data < 5:
            allowed = False
        response = aiohttp_jinja2.render_template("cog_pages/cogmanager/add_path.html", request, {"can": allowed})
        return response

    @login_required
    async def cogs_cogmanager(self, request):
        context = self.get_context("cogmanager")
        response = aiohttp_jinja2.render_template("cog_pages/cogmanager.html", request, context)
        return response

    @login_required
    async def cogs_admin_announce_action(self, request):
        data = await get_permissions(self, request)
        if data > 10:
            data -= 10
        if data < 5:
            return web.json_response(status=403)
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

    @login_required
    async def cogs_admin_announce(self, request):
        data = await get_permissions(self, request)
        allowed = True
        if data > 10:
            data -= 10
        if data < 5:
            allowed = False
        response = aiohttp_jinja2.render_template("cog_pages/admin/announce.html", request, {"can": allowed})
        return response

    @login_required
    async def cogs_admin_serverlock_action(self, request):
        data = await get_permissions(self, request)
        if data > 10:
            data -= 10
        if data < 5:
            return web.json_response(status=403)
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

    @login_required
    async def cogs_admin_serverlock(self, request):
        data = await get_permissions(self, request)
        allowed = True
        if data > 10:
            data -= 10
        if data < 5:
            allowed = False
        response = aiohttp_jinja2.render_template("cog_pages/admin/serverlock.html", request, {"can": allowed})
        return response

    @login_required
    async def cogs_admin(self, request):
        context = self.get_context("admin")
        response = aiohttp_jinja2.render_template("cog_pages/admin.html", request, context)
        return response

    @login_required
    async def cogs_mod_unignore_action(self, request):
        data = await get_permissions(self, request)
        if data > 10:
            data -= 10
        if data < 3:
            return web.json_response(status=403)
        data = await get_specific_perms(self, request, (await request.json())["thing"])
        if data < 3:
            return web.json_response({"message": "You can't use ignore in that guild"})
        data = await request.json()
        mtype = data["type"]
        specifier = data["sp"]
        identifier = data["thing"]
        try:
            ignored = await unignore(self.bot, mtype, specifier, identifier)
        except Exception as e:
            data = {
                "message": str(e)
            }
        else:
            if ignored:
                data = {
                    "message": "Now unignored."
                }
            else:
                data = {
                    "message": f"This {mtype} was already unignored."
                }
        return web.json_response(data)

    @login_required
    async def cogs_mod_ignore_action(self, request):
        data = await get_permissions(self, request)
        if data > 10:
            data -= 10
        if data < 3:
            return web.json_response(status=403)
        data = await get_specific_perms(self, request, (await request.json())["thing"])
        if data < 3:
            return web.json_response({"message": "You can't use ignore in that guild"})
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

    @login_required
    async def cogs_mod_unignore(self, request):
        data = await get_permissions(self, request)
        allowed = True
        if data > 10:
            data -= 10
        if data < 3:
            allowed = False
        response = aiohttp_jinja2.render_template("cog_pages/mod/unignore.html", request, {"can": allowed})
        return response

    @login_required
    async def cogs_mod_ignore(self, request):
        data = await get_permissions(self, request)
        allowed = True
        if data > 10:
            data -= 10
        if data < 3:
            allowed = False
        response = aiohttp_jinja2.render_template("cog_pages/mod/ignore.html", request, {"can": allowed})
        return response

    @login_required
    async def cogs_mod(self, request):
        context = self.get_context("mod")
        response = aiohttp_jinja2.render_template("cog_pages/mod.html", request, context)
        return response

    async def _credits(self, request):
        response = aiohttp_jinja2.render_template("credits.html", request, {})
        return response

    @web.middleware
    async def error_middleware(self, request, handler):
        # For handling 404s
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
        self.app.router.add_get("/", self.home)
        self.port = await self.cog.conf.port()

        # Main pages
        self.app.router.add_get("/dashboard", self.dashboard)
        self.app.router.add_get("/credits", self._credits)
        self.app.router.add_get("/cogs", self.cogs)
        self.app.router.add_get("/errors/action", self.errors_action)
        self.app.router.add_get("/login", self.login)
        self.app.router.add_post("/login/action", self.login_action)
        self.app.router.add_get("/useCode", self.use_code)
        self.app.router.add_get("/monitor", self.monitor_time)

        # Errors
        self.app.router.add_get("/errors", self.errors)
        self.app.router.add_get("/errors/view", self.error_view)
        self.app.router.add_post("/errors/view/action", self.error_view_action)
        self.app.router.add_post("/errors/remove/action", self.error_remove_action)

        # Mod
        self.app.router.add_get("/cogs/mod", self.cogs_mod)
        self.app.router.add_get("/cogs/mod/ignore", self.cogs_mod_ignore)
        self.app.router.add_post("/cogs/mod/ignore/action", self.cogs_mod_ignore_action)
        self.app.router.add_get("/cogs/mod/unignore", self.cogs_mod_unignore)
        self.app.router.add_post("/cogs/mod/unignore/action", self.cogs_mod_unignore_action)

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

        # Static

        self.app['static_root_url'] = str(self.path / "static")
        aiohttp_jinja2.setup(self.app,
            loader=jinja2.FileSystemLoader(str(self.path / "templates")))
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.handler = self.app.make_handler()
        self.site = web.TCPSite(self.runner, "0.0.0.0", self.port)
        await self.site.start()
        print("Dashboard up!")