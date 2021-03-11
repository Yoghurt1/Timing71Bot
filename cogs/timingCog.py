from discord import Member, utils
from discord.ext import commands
from concurrent.futures import ThreadPoolExecutor
from discord_config import Settings
import json
import nest_asyncio
import asyncio

nest_asyncio.apply()

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
		self.loop = asyncio.get_event_loop()

	@commands.command()
	async def events(self, ctx):
		res = await self.bot.timingClient.events(self.loop)
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
	async def car(self, ctx, carNum):
		asyncio.run_coroutine_threadsafe(self.bot.timingClient.getCarDetails(carNum, ctx), self.loop)

	@commands.command()
	@commands.is_owner()
	async def setAdminRole(self, ctx, roleName):
		self._config.set('adminRole', roleName)
		self._config.save()
		await ctx.send("Set admin role to " + roleName)

	@commands.command()
	@commands.is_owner()
	async def setModRole(self, ctx, roleName):
		self._config.set("modRole", roleName)
		self._config.save()
		await ctx.send("Set mod role to " + roleName)

	@commands.command()
	@commands.has_any_role(_config.adminRole, _config.modRole)
	async def setDelay(self, ctx, delay):
		self._config.set('delay', delay)
		self._config.save()
		await ctx.send("Set delay to " + delay)

	@commands.command()
	async def bulg(self, ctx):
		await ctx.send("🛌")

	@commands.command()
	async def broc(self, ctx):
		await ctx.send("https://media.discordapp.net/attachments/731131954728009760/771875090768855050/unknown.png")

	@commands.command()
	@commands.has_any_role(_config.adminRole, _config.modRole)
	async def channel(self, ctx):
		await ctx.send("https://media.discordapp.net/attachments/293550896950935552/804399368638824479/Wrong_channel.jpg?width=744&height=380")

def setup(bot):
	bot.add_cog(TimingCog(bot))