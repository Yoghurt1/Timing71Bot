from discord import DMChannel, Thread
from discord.ext import commands
from discord_config import Settings
import logging


class TimingCog(commands.Cog):
    _config = Settings(
        defaults={
            "adminRole": "Admin",
            "modRole": "Tiddy Boiz",
            "delay": 0,
            "excludes": [],
        },
        filename="config.json",
    )

    def __init__(self, bot, config=None):
        self.bot = bot

    @commands.command()
    async def events(self, ctx):
        res = self.bot.timingClient.events()
        await ctx.send(res)

    @commands.command()
    @commands.has_any_role(_config.adminRole, _config.modRole)
    async def bindevent(self, ctx, eventNum):
        connectMsg = await ctx.send("Connecting to event number " + str(eventNum) + ".")
        await self.bot.timingClient.connectToEvent(eventNum, connectMsg)

    @bindevent.error
    async def bindEventError(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("You haven't provided an event number, genius.")

    @commands.command()
    @commands.has_any_role(_config.adminRole, _config.modRole)
    async def unbind(self, ctx):
        await ctx.send("Unbinding, I'll be available again shortly.")
        await self.bot.timingClient.closeEvent()

    @commands.command()
    @commands.check(threadCheck)
    async def car(self, ctx, carNum, spec=None):
        await self.bot.timingClient.getCarDetails(ctx, carNum, spec)

    @car.error
    async def carError(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send(
                "Try specifiying a car number next time, and I'll think about it."
            )

    @commands.command()
    @commands.check(threadCheck)
    async def trackinfo(self, ctx):
        await self.bot.timingClient.getTrackInfo(ctx)

    @commands.command()
    @commands.check(threadCheck)
    async def whois(self, ctx, carNum):
        await self.bot.timingClient.whoIsCar(ctx, carNum)

    @commands.command()
    @commands.has_any_role(_config.adminRole, _config.modRole)
    async def setdelay(self, ctx, delay):
        self.bot.timingClient.setDelay(delay)
        await ctx.send("Delay set to " + delay + " seconds.")

    @commands.command()
    async def delay(self, ctx):
        await ctx.send(
            "Delay is currently set to "
            + self.bot.timingClient.getDelay()
            + " seconds."
        )

    @commands.command()
    @commands.has_any_role(_config.adminRole, _config.modRole)
    async def addexclude(self, ctx, exclude):
        self.bot.timingClient.addExclude(exclude)
        await ctx.send("Added " + exclude + " to excludes list.")

    @commands.command()
    async def excludes(self, ctx):
        await ctx.send(self.bot.timingClient.getExcludes())

    @commands.command()
    @commands.has_any_role(_config.adminRole, _config.modRole)
    async def clearexcludes(self, ctx):
        self.bot.timingClient.clearExcludes()
        await ctx.send("Cleared excludes.")


def setup(bot):
    bot.add_cog(TimingCog(bot))


def threadCheck(ctx):
    return isinstance(ctx.channel, Thread)
