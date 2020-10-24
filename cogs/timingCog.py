from discord import Member, utils
from discord.ext import commands
import json
import nest_asyncio
import asyncio

nest_asyncio.apply()

class TimingCog(commands.Cog):
	_config = json.load(open("config.json", "r"))

	def __init__(self, bot, config=None):
		self.bot = bot

	def updateConfig(self, config):
		json.dump(config, open("config.json", "w"))
		self._config = config
	
	async def messageWorker(self, ctx):
		while True:
			msg = "**" + self.bot.timingClient.getCurrentEvent() + "**\n" + self.bot.timingClient.msgQueue.get(False, 3)
			await ctx.send(msg)
			self.bot.timingClient.msgQueue.task_done()

	@commands.command()
	async def events(self, ctx):
		res = await self.bot.timingClient.menu()
		await ctx.send(res)

	@commands.command()
	@commands.has_any_role(_config["adminRole"], _config["modRole"])
	async def bindEvent(self, ctx, eventNum):
		try:
			int(eventNum)
		except:
			return await ctx.send("Invalid event.")

		await ctx.send("Connecting to event number " + str(eventNum) + ".")
		loop = asyncio.get_running_loop()
		asyncio.run_coroutine_threadsafe(self.messageWorker(ctx), loop)
		await self.bot.timingClient.connectToEvent(eventNum)

	@bindEvent.error
	async def bindEventError(self, ctx, error):
		if isinstance(error, commands.MissingRequiredArgument):
			return await ctx.send("You haven't provided an event number, genius.")
		elif isinstance(error, commands.MissingAnyRole):
			return await ctx.send("You aren't cool enough to use this command.")

	@commands.command()
	@commands.has_any_role(_config["adminRole"], _config["modRole"])
	async def unbind(self, ctx):
		await self.bot.timingClient.unsubscribe()
		await ctx.send("Unsubscribed.")
	
	@commands.command()
	async def recordings(self, ctx):
		res = self.bot.timingClient.getRecordings()
		print(res)
		await ctx.send(str(res))

	@commands.command()
	@commands.is_owner()
	async def setAdminRole(self, ctx, roleName):
		self._config["adminRole"] = roleName
		self.updateConfig(self._config)
		await ctx.send("Set admin role to " + roleName)

	@commands.command()
	@commands.is_owner()
	async def setModRole(self, ctx, roleName):
		self._config["modRole"] = roleName
		self.updateConfig(self._config)
		await ctx.send("Set mod role to " + roleName)

	@commands.command()
	async def bulg(self, ctx):
		await ctx.send("🛌")

def setup(bot):
	bot.add_cog(TimingCog(bot))