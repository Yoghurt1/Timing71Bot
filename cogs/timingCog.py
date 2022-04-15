from discord import DMChannel, Thread
from discord.ext import commands
from discord_config import Settings
import logging


def threadCheck(ctx):
    return isinstance(ctx.channel, Thread)


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
    async def connect(self, ctx, eventNum):
        connectMsg = await ctx.send("Connecting to event number " + str(eventNum) + ".")
        await self.bot.timingClient.connectToEvent(eventNum, ctx, connectMsg)

    @connect.error
    async def connectError(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.send("You haven't provided an event number, genius.")

    @commands.command()
    @commands.has_any_role(_config.adminRole, _config.modRole)
    async def disconnect(self, ctx):
        await ctx.send("Disconnecting, I'll be available again shortly.")
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


def setupHelp(cog: TimingCog):
    cog.events.brief = "Fetch current events"
    cog.events.help = "Will pull a list of events that are ongoing on Timing71 and display them with their respective event numbers. The associated numbers can then be used with .bindevent to connect to the associated event. If there are no events ongoing, a message indicating such will be returned."

    cog.connect.brief = "Connect to an event"
    cog.connect.help = "Connects to an event with the event number as specified in the response from the .events command. It will then create a new thread where all timing events will be posted. Users cannot post anything in this thread other than other command invokations, such as .car or .whois."
    cog.connect.usage = "\n\nSyntax: .connect <event_number>"

    cog.car.brief = "Get car details"
    cog.car.help = "Get details about a car partaking in the current event. By default, it will return all the information about a given participant, however this can be refined with the optional `spec` parameter. For example, `.car 1 lap` would return any fields that have 'lap' in the field description, e.g. laps completed, last lap time, and best lap time."
    cog.car.usage = "\n\nSyntax: .car <car_number> [filter]"

    return cog


async def setup(bot):
    timingCog = setupHelp(TimingCog(bot))

    await bot.add_cog(timingCog)
