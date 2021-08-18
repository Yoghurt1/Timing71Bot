from discord import DMChannel
from discord.ext import commands
from discord_config import Settings
import logging

class TimingCog(commands.Cog):
	_config = Settings(defaults={
			"adminRole": "Admin",
			"modRole": "Tiddy Boiz",
			"delay": 0,
			"excludes": []
		},
		filename="config.json"
	)

	def __init__(self, bot, config=None):
		self.bot = bot

	@commands.command()
	async def events(self, ctx):
		res = self.bot.timingClient.events()
		await ctx.send(res)

	@commands.command()
	@commands.has_any_role(_config.adminRole, _config.modRole)
	async def bindEvent(self, ctx, eventNum):
		await ctx.send("Connecting to event number " + str(eventNum) + ".")
		await self.bot.timingClient.connectToEvent(eventNum, ctx)

	@bindEvent.error
	async def bindEventError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			return await ctx.send("You haven't provided an event number, genius.")

	@commands.command()
	@commands.has_any_role(_config.adminRole, _config.modRole)
	async def unbind(self, ctx):
		await ctx.send("Unbinding, I'll be available again shortly.")
		await self.bot.timingClient.closeEvent()
	
	@commands.command()
	async def car(self, ctx, carNum, spec=None):
		if isinstance(ctx.channel, DMChannel) or ctx.channel.name == "bot_log":
			logging.info(".car command called by {0} with args: {1}, {2}".format(ctx.author, carNum, spec))
			await self.bot.timingClient.getCarDetails(ctx, carNum, spec)
		else:
			logging.error(".car command called outside PMs or #bot_log by {0}".format(ctx.author))

	@commands.command()
	async def trackInfo(self, ctx):
		await self.bot.timingClient.getTrackInfo(ctx)
	
	@commands.command()
	async def whois(self, ctx, carNum):
		await self.bot.timingClient.whoIsCar(ctx, carNum)

	@commands.command()
	@commands.has_any_role(_config.adminRole, _config.modRole)
	async def setDelay(self, ctx, delay):
		self.bot.timingClient.setDelay(delay)
		await ctx.send("Delay set to " + delay + " seconds.")

	@commands.command()
	async def delay(self, ctx):
		await ctx.send("Delay is currently set to " + self.bot.timingClient.getDelay() + " seconds.")

	@commands.command()
	@commands.has_any_role(_config.adminRole, _config.modRole)
	async def addExclude(self, ctx, exclude):
		self.bot.timingClient.addExclude(exclude)
		await ctx.send("Added " + exclude + " to excludes list.")

	@commands.command()
	async def excludes(self, ctx):
		await ctx.send(self.bot.timingClient.getExcludes())

	@commands.command()
	@commands.has_any_role(_config.adminRole, _config.modRole)
	async def clearExcludes(self, ctx):
		self.bot.timingClient.clearExcludes()
		await ctx.send("Cleared excludes.")

def setup(bot):
	bot.add_cog(TimingCog(bot))