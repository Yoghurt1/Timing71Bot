import logging
from discord.ext import commands

class DiscordClient(commands.Bot):
	async def on_ready(self):
		logging.info('We have logged in as {0.user}'.format(self))
		await self.timingClient.fetchEvents()

	def __init__(self, timingClient):
		super().__init__(command_prefix=".")

		self.timingClient = timingClient
		self.load_extension("cogs.timingCog")
		self.load_extension("cogs.managementCog")

	async def on_command_error(self, ctx, exception):
		logging.error("Command failed with {0} error: {1}".format(type(exception), exception))

		if isinstance(exception, commands.MissingAnyRole):
			await ctx.send("You aren't cool enough to use this command.")
		elif isinstance(exception, commands.CommandOnCooldown):
			await ctx.send("Have some patience, child. {0}.".format(exception))
		elif isinstance(exception, commands.CommandInvokeError):
			await ctx.send("Unknown error occurred. Good job, idiot.")

	async def on_disconnect(self):
		print("Discord client disconnecting")
