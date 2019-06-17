from redbot.core import commands, checks, Config
from redbot.core.data_manager import bundled_data_path
from redbot.core.utils.menus import menu, DEFAULT_CONTROLS
import discord
import traceback
import asyncio
from .webserver import WebServer


class Dashboard(commands.Cog):

    __version__ = "0.3.4a"
    __red__ = ["3.0.0", "3.1.1"]

    def __init__(self, bot):
        self.bot = bot
        self.conf = Config.get_conf(self, identifier=473541068378341376)
        self.conf.register_global(
            errors=[],
            command_errors=[],
            logerrors=False,
            secret="",
            errorpass=[],
            redirect="http://localhost:42356",
            owner_perm=15,
            port=42356,
            widgets=[],
            testwidgets=[],
            support="",
        )
        self.bot.add_listener(self.error, "on_command_error")
        self.web = WebServer(self.bot, self)
        self.path = bundled_data_path(self)
        self.web_task = self.bot.loop.create_task(self.web.make_webserver(self.path))

    def cog_unload(self):
        self.__unload()

    def __unload(self):
        self.web_task.cancel()
        self.web.unload()

    async def error(self, ctx, error):
        if not (await self.conf.logerrors()):
            return
        if isinstance(error, commands.CommandInvokeError):
            exception_log = f"Error in command {ctx.command.qualified_name}\n"
            exception_log += "".join(
                traceback.format_exception(type(error), error, error.__traceback__)
            )
            command_errors = await self.conf.command_errors()
            data = {
                "invoker": f"{str(ctx.author)} <@{ctx.author.id}>",
                "command": f"{ctx.command.qualified_name}",
                "error": exception_log,
                "id": len(command_errors) + 1,
                "short": str(error),
            }
            async with self.conf.command_errors() as errors:
                errors.append(data)

    @commands.group()
    async def dashboard(self, ctx):
        """Group command for controlling the web dashboard for Red"""
        pass

    @checks.is_owner()
    @dashboard.command()
    async def restart(self, ctx, wait: int = 0):
        """Restarts the webserver, kicking everyone offline.
		
		Pass a wait argument to make it wait that many seconds before coming back online."""
        self.__unload()
        await ctx.send("Stopped the webserver.")
        await asyncio.sleep(wait)
        from .webserver import WebServer

        self.web = WebServer(self.bot, self)
        self.web_task = self.bot.loop.create_task(self.web.make_webserver(self.path))
        await ctx.send("Webserver has been restarted.")

    @checks.is_owner()
    @dashboard.group()
    async def settings(self, ctx):
        """Group command for setting up the web dashboard for this Red bot"""
        pass

    @settings.command()
    async def logerrors(self, ctx, log: bool):
        """Log errors in the bot to display on the dashboard."""
        await self.conf.logerrors.set(log)
        if log:
            return await ctx.send("This cog will now log command errors.")
        await ctx.send("This cog will no longer log command errors.")

    @settings.command()
    async def port(self, ctx, port: int):
        """Sets the port for the webserver to be run on.
		
		You will need to reload the cog for changes to take effect."""
        if (port < 1) or (port > 65535):
            return await ctx.send("Invalid port number.  The port must be between 1 and 65535.")
        await self.conf.port.set(port)
        await ctx.send(
            f"Port set.  Please run `{ctx.prefix}dashboard restart` for the change to take effect."
        )

    @settings.command()
    async def support(self, ctx, url: str = ""):
        """Set the URL for support.  This is recommended to be a Discord Invite.

        Leaving it blank will remove it."""
        await self.conf.support.set(url)
        await ctx.tick()

    @settings.group()
    async def oauth(self, ctx):
        """Group command for changing the settings related to Discord OAuth."""
        pass

    @oauth.command()
    async def secret(self, ctx, *, secret: str):
        """Set the client secret needed for Discord Oauth."""
        await self.conf.secret.set(secret)
        await ctx.tick()

    @oauth.command()
    async def redirect(self, ctx, redirect: str):
        """Set the redirect for after logging in via Discord OAuth."""
        await self.conf.redirect.set(redirect)
        await ctx.tick()

    @settings.group()
    async def ui(self, ctx):
        """Group command for controlling widgets on the main page of the dashboard."""
        pass

    @ui.command(name="view")
    async def ui_view(self, ctx):
        """View the widgets added to the main page of the dashboard."""
        widgets = await self.conf.widgets()
        if not widgets:
            return await ctx.send("You have not added any widgets.")
        messages = []
        for number, wid in enumerate(widgets, 1):
            messages.append(f"{number}.```html\n{wid}```")
        await menu(ctx, messages, DEFAULT_CONTROLS)

    @ui.command()
    async def add(self, ctx):
        """Add a widget to the main page of the dashboard.

        Note that this requires HTML knowledge.  A builder may come in the future to help people who don't know HTML."""
        await ctx.send(
            "Enter the text that you would like to be in the new widget.  Note that you should have HTML knowledge"
            " before doing this."
        )

        def check(m):
            return (m.author.id == ctx.author.id) and (m.channel.id == ctx.channel.id)

        try:
            message = await self.bot.wait_for("message", check=check, timeout=600.0)
        except asyncio.TimeoutError:
            return await ctx.send("Command timed out.")
        async with self.conf.testwidgets() as var:
            var.append(message.content)
        await ctx.send(
            "Widget added to testing.  You can view the widget at the dashboard's root URL + /widgettest.  "
            "For example, if my URL was http://localhost:42356, then the testing page would be at http://localhost:42356/widgettest.  Respond back with `y` or `n` here if you are okay with the additions."
        )

        def check_two(m):
            return check(m) and (m.content[0].lower() in ["y", "n"])

        try:
            msg = await self.bot.wait_for("message", check=check_two, timeout=600.0)
        except asyncio.TimeoutError:
            await ctx.send("Timed out.  Removing from test page.")
            async with self.conf.testwidgets() as var:
                var.remove(message.content)
            return
        async with self.conf.testwidgets() as var:
            var.remove(message.content)
        if msg.content[0].lower() == "n":
            return await ctx.send(
                "Not adding to main page.  The widget was also removed from the test page."
            )
        else:
            async with self.conf.widgets() as var:
                var.append(message.content)
            return await ctx.send("Removed widget from test page and added to main page.")

    @ui.command()
    async def remove(self, ctx, number: int):
        """Remove a certain widget from the main page.

        The number must be the number taken from `[p]dashboard settings ui view`."""
        widgets = await self.conf.widgets()
        try:
            widget = widgets[number - 1]
        except IndexError:
            return await ctx.send("You don't have a widget with that number")
        await ctx.send(
            f"You are about to delete the widget with this code.  Are you sure?```html\n{widget}```"
        )

        def check(m):
            return (
                (m.author.id == ctx.author.id)
                and (m.channel.id == ctx.channel.id)
                and (m.content[0].lower() in ["y", "n"])
            )

        try:
            message = await self.bot.wait_for("message", check=check, timeout=60.0)
        except asyncio.TimeoutError:
            return await ctx.send("Timed out.  Not removing.")
        if message.content[0].lower() == "n":
            return await ctx.send("Not removing.")
        else:
            del widgets[number - 1]
            await self.conf.widgets.set(widgets)
            await ctx.send("Successfully removed widget.")

    @settings.command()
    async def view(self, ctx):
        """View the current dashboard settings."""
        embed = discord.Embed(title="Red V3 Dashboard Settings", color=0x0000FF)
        log = await self.conf.logerrors()
        if ctx.guild:
            secret = "[REDACTED]"
        else:
            secret = await self.conf.secret()
        redirect = await self.conf.redirect()
        port = await self.conf.port()
        support = await self.conf.support()
        description = (
            f"Error logging enabled: |  {log}\n"
            f"Client Secret:         |  {secret}\n"
            f"Redirect URI:          |  {redirect}\n"
            f"Port Number:           |  {port}\n"
            f"Support Server:        |  {support}"
        )
        embed.description = "```py\n" + description + "```"
        embed.set_footer(text="Dashboard created by Neuro Assassin")
        await ctx.send(embed=embed)
