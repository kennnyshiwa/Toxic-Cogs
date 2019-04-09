from redbot.core import commands, checks, Config
from redbot.core.data_manager import cog_data_path
import discord
import asyncio
import logging
from aiohttp import web
from .webserver import WebServer
from aiohttp_json_rpc import JsonRpcClient

class Dashboard(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.conf = Config.get_conf(self, identifier=473541068378341376)
		self.web = WebServer(bot, self)
		self.path = cog_data_path(self)
		default_global = {
			"username": "",
			"password": "",
			"port": 42356,
			"message": 0
		}
		#setup_routes(self.app)
		#runner = web.AppRunner(self.app)
		self.conf.register_global(**default_global)
		self.rpc_task = self.bot.loop.create_task(self.initialize())
		self.web_task = self.bot.loop.create_task(self.web.make_webserver(self.path))
		self.rpc_client = JsonRpcClient(logger=logging.getLogger('red'))

	def __unload(self):
		try:
			#self.rpc_client.disconnect()
			self.rpc_task.cancel()
			self.web_task.cancel()
			self.web.__unload()
		except Exception as e:
			print(e)
		del self.rpc_client

	async def initialize(self):
		print("Initializing")
		await self.bot.wait_until_ready()
		print("Ready")
		await self.rpc_client.connect('127.0.0.1', 6133)
		print("Connected")
		call_result = await self.rpc_client.call('CORE__LOAD', {"cog_names": ["filter"], "kwargs": {}})
		print(type(self.rpc_client))
		return
		"""
		port = await self.conf.port()
		new_loop = asyncio.new_event_loop()
		asyncio.set_event_loop(new_loop)
		await self.app.app.create_server(host="0.0.0.0", port=port)
		asyncio.set_event_loop(self.bot.loop)
		"""

	@commands.group()
	async def dashboard(self, ctx):
		"""Group command for controlling the web dashboard for Red"""
		pass

	@checks.is_owner()
	@dashboard.group()
	async def settings(self, ctx):
		"""Group command for setting up the web dashboard for this Red bot"""
		pass

	@settings.command()
	async def setup(self, ctx):
		"""Basic set up the web server for this Red bot"""
		await ctx.send("DMing you to set up the web dashboard...")
		try:
			await ctx.author.send("Please input the username required to log into the web dashboard.")
		except discord.errors.Forbidden:
			return await ctx.send("I am unable to DM you.  Make sure you do not have me blocked.")
		def check(m):
			return (m.guild == None) and (m.author.id == ctx.author.id)
		try:
			username = await self.bot.wait_for("message", check=check, timeout=60.0)
		except asyncio.TimeoutError:
			return await ctx.author.said("Command timed out.")
		await ctx.author.send("Please input the password required to log into the web dashboard.")
		try:
			password = await self.bot.wait_for("message", check=check, timeout=60.0)
		except asyncio.TimeoutError:
			return await ctx.author.said("Command timed out.")
		if (len(username.content) <= 5) or (len(password.content) <= 5):
			return await ctx.author.send("Please choose a username or password that has over 5 characters.")
		await ctx.author.send(f"You are about to set the username to: `{username.content}` and the password to `{password.content}`.  You will still be required to enter the Discord ID of the bot when logging in.  Are you sure you want to set the username and password to this? (y/n)")
		def check2(m):
			return (m.guild == None) and (m.author.id == ctx.author.id) and (m.content.lower()[0] in ["y", "n"])
		try:
			confirm = await self.bot.wait_for("message", check=check2, timeout=60.0)
		except asyncio.TimeoutError:
			return await ctx.author.said("Command timed out.")
		if confirm.content.lower().startswith("y"):
			await self.conf.username.set(username.content)
			await self.conf.password.set(password.content)

	@settings.command(aliases=["cm"])
	async def commandmessage(self, ctx):
		"""Uses this message/command for invoking commands through the dashboard"""
		await self.conf.message.set(ctx.message.id)
		await ctx.send("Message ID has been set.")