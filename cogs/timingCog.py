from discord import Member
from discord.ext import commands
import json

class TimingCog(commands.Cog):
	_events = []
	with open("config.json") as configFile:
		_config = json.load(configFile)

	def __init__(self, bot, config=None):
		self.bot = bot
		

	@commands.command()
	async def events(self, ctx):
		self._events = self.bot.timingClient.fetchEvents()
		if self._events != None:
			return await ctx.send(await self.bot.timingClient.menu(self._events))
		else:
			return await ctx.send("Failed to fetch events.")

	@commands.command()
	@commands.has_any_role(_config["adminRole"], _config["modRole"])
	async def bindEvent(self, ctx, eventNum):
		try:
			int(eventNum)
			self._events[eventNum]
		except:
			return await ctx.send("Invalid event.")
			
		selectedEvent = self._events[eventNum - 1]
		await self.bot.timingClient.subscribeToEvent(selectedEvent)

	@bindEvent.error
	async def bindEventError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			return await ctx.send("You haven't provided an event number, genius.")
		elif isinstance(error, commands.MissingAnyRole):
			return await ctx.send("You aren't cool enough to use this command.")


def setup(bot):
	bot.add_cog(TimingCog(bot))