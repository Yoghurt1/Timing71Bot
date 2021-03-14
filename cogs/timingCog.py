from discord.ext import commands
from discord_config import Settings

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
		res = await self.bot.timingClient.events()
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
		self._config.set("delay", 0)
		self.bot.timingClient.unbind()
	
	@commands.command()
	@commands.cooldown(1, 20)
	async def car(self, ctx, carNum, spec=None):
		await self.bot.timingClient.getCarDetails(ctx, carNum, spec)

def setup(bot):
	bot.add_cog(TimingCog(bot))