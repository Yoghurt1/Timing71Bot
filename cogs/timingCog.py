from discord import DMChannel
from discord.ext import commands
from discord_config import Settings
import logging

class TimingCog(commands.Cog):
	_config = Settings(defaults={
			"adminRole": "Admin",
			"modRole": "Tiddy Boiz",
			"delay": 0
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
		else:
			return await ctx.send("Unknown error occured.")

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

def setup(bot):
	bot.add_cog(TimingCog(bot))