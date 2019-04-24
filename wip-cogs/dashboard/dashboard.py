from redbot.core import commands, checks, Config
from redbot.core.data_manager import bundled_data_path
import discord
import traceback
import asyncio
import logging
from aiohttp import web
from .webserver import WebServer

class Dashboard(commands.Cog):

	__version__ = "0.3.2a"
	__red__ = "3.0.0"

	def __init__(self, bot):
		self.bot = bot
		self.conf = Config.get_conf(self, identifier=473541068378341376)
		self.conf.register_global(errors=[], command_errors=[], logerrors=False, secret="", errorpass=[])
		self.bot.add_listener(self.error, "on_command_error")
		self.web = WebServer(self.bot, self)
		self.path = bundled_data_path(self)
		self.web_task = self.bot.loop.create_task(self.web.make_webserver(self.path))

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
				"short": str(error)
			}
			async with self.conf.command_errors() as errors:
				errors.append(data)

	@commands.group()
	async def dashboard(self, ctx):
		"""Group command for controlling the web dashboard for Red"""
		pass

	@checks.is_owner()
	@dashboard.command()
	async def restart(self, ctx, wait: int=0):
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
		"""Log errors in the bot to display on the dashboard"""
		await self.conf.logerrors.set(log)
		if log:
			return await ctx.send("This cog will now log command errors.")
		await ctx.send("This cog will no longer log command errors.")

	@settings.command()
	async def secret(self, ctx, *, secret: str):
		"""Set the client secret needed for Discord Oauth."""
		await self.conf.secret.set(secret)
		await ctx.tick()