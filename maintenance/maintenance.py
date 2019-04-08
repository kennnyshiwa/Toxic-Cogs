from redbot.core import commands, checks, Config
from .converters import Margs
from datetime import datetime
import asyncio
import discord
import time


class Maintenance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conf = Config.get_conf(self, identifier=473541068378341376)
        default_global = {
            "on": [False, 0, []],
            "message": "The bot is undergoing maintenance.  Please check back later.",
            "delete": 3,
            "scheduledmaintenance": [],
        }
        # When on maintenance, on will be set to [True, second of when it is off maintenance, list of people who can bypass the maintenance]
        self.conf.register_global(**default_global)
        self.bot.add_check(self.cog_check)
        self.task = self.bot.loop.create_task(self.bg_loop())

    def __unload(self):
        self.bot.remove_check(self.cog_check)
        self.task.cancel()

    async def bg_loop(self):
        await self.bot.wait_until_ready()
        while self == self.bot.get_cog("Maintenance"):
            scheduled = await self.conf.scheduledmaintenance()
            setting = []
            for entry in scheduled:
                if entry[0] <= time.time():
                    await self.conf.on.set([True, entry[1], entry[2]])
                else:
                    setting.append(entry)
            await self.conf.scheduledmaintenance.set(setting)
            await asyncio.sleep(5)

    async def cog_check(self, ctx):
        on = await self.conf.on()
        if not on[0]:
            return True
        if on[1] <= time.time() and on[1] != 0:
            setting = [False, 0, []]
            await self.conf.on.set(setting)
            return True
        on[2].append(self.bot.owner_id)
        if ctx.author.id in on[2]:
            return True
        message = await self.conf.message()
        delete = await self.conf.delete()
        if delete != 0:
            await ctx.send(message, delete_after=delete)
        else:
            await ctx.send(message)
        return False

    @checks.is_owner()
    @commands.group()
    async def maintenance(self, ctx):
        """Control the bot's maintenance."""
        pass

    @maintenance.command(name="on")
    async def _on(self, ctx, *, args: Margs = None):
        """Puts the bot on maintenance, preventing everyone but you and people whitelisted from running commands.  Other people will just be told the bot is currently on maintenance.
        
        You can use the following arguments to specify things:
            --start-in: Makes the maintenace start in that long.
            --end-in: Schedules the maintenance to end in that long from the current second.
            --end-after: Schedules the maintenance to end in that long after the maitenance has started.
            --whitelist: Provide user IDs after this to whitelist people from the maintenance.
            
        Examples:
        `[p]maintenance on --start-in 5 seconds`; starts a maintenance in 5 seconds
        `[p]maintenance on --start-in 5 seconds --end-in 10 seconds`; starts a maintenance in 5 seconds, then scheduled to end in 10 seconds, so it will only be on maintenance for 5 seconds.
        `[p]maintenance on --start-in 10 seconds --end-after 10 seconds --whitelist 473541068378341376 473541068378341377`; starts a maintenance in 10 seconds, that lasts for 10 seconds after, and has the two user IDs who are exempted from the maintenance."""
        on = await self.conf.on()
        if on[0]:
            return await ctx.send(
                f"The bot is already on maintenance.  Please clear with `{ctx.prefix}maintenance off`"
            )
        scheduled = await self.conf.scheduledmaintenance()
        if args:
            num = args.end
            whitelist = args.whitelist
            start = args.start
        else:
            num = 0
            whitelist = []
            start = time.time()
        if start == time.time():
            setting = [True, num, whitelist]
            await self.conf.on.set(setting)
        else:
            scheduled.append([start, args.end, whitelist])
            await self.conf.scheduledmaintenance.set(scheduled)
        await ctx.tick()

    @maintenance.command()
    async def settings(self, ctx):
        """Tells the current settings of the cog."""
        on = await self.conf.on()
        scheduled = await self.conf.scheduledmaintenance()
        message = await self.conf.message()
        delete = await self.conf.delete()
        sending = (
            f"Messages are deleted after {delete} seconds.  "
            f"Your current disabled message is ```{message}```"
        )
        if not on[0]:
            sending += "The bot is currently not on maintenance."
            if len(scheduled) != 0:
                sending += "  The following maintenances are scheduled for:```\n"
                for x in scheduled:
                    starting = str(datetime.fromtimestamp(x[0]).strftime("%A, %B %d, %Y %I:%M:%S"))
                    sending += "    • " + starting
                sending += "```"
            return await ctx.send(sending)
        if on[1] != 0:
            done = str(datetime.fromtimestamp(on[1]).strftime("%A, %B %d, %Y %I:%M:%S"))
            done = "on " + done
        else:
            done = "when the bot owner removes it from maintenance"
        users = []
        for user in on[2]:
            user_profile = await self.bot.get_user_info(user)
            users.append(user_profile.display_name) if hasattr(
                user_profile, "display_name"
            ) else users.append(f"<removed user {user}>")
        sending += "The bot is currently under maintenance.  " f"It will be done {str(done)}.  "
        sending += (
            f"The following users are whitelisted from the maintenance: `{'` `'.join(users)}`."
            if len(users) != 0
            else "No users are whitelisted from the maintenance."
        )
        await ctx.send(sending)

    @maintenance.command()
    async def off(self, ctx):
        """Clears the bot from maintenance"""
        on = await self.conf.on()
        if not on[0]:
            return await ctx.send("The bot is not on maintenance.")
        setting = [False, 0, []]
        await self.conf.on.set(setting)
        await ctx.tick()

    @maintenance.command()
    async def message(self, ctx, *, message):
        """Set the message sent when the bot is down for maintenance"""
        await self.conf.message.set(message)
        await ctx.tick()

    @maintenance.command()
    async def deleteafter(self, ctx, amount: int = 0):
        """Set the amount of seconds before the maintenance message is deleted.  Pass no parameter or 0 to make it not delete the message"""
        await self.conf.delete.set(amount)
        await ctx.tick()

    @maintenance.command()
    async def whitelist(self, ctx, user: discord.User):
        """Remove or add a person from or to the whitelist for the current maintenance"""
        on = await self.conf.on()
        if user.id in on[2]:
            on[2].remove(user.id)
            message = f"{user.display_name} has been removed from the whitelist."
        else:
            on[2].append(user.id)
            message = f"{user.display_name} has been added to the whitelist."
        await self.conf.on.set(on)
        await ctx.send(message)