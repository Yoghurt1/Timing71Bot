import json
import logging
from discord import Member
from discord.ext import commands
from cogs.timingCog import TimingCog

class DiscordClient(commands.Bot):
	async def on_ready(self):
		logging.info('We have logged in as {0.user}'.format(self))

	def __init__(self, timingClient):
		super().__init__(command_prefix=".")

		self.timingClient = timingClient
		self.load_extension("cogs.timingCog")

	async def on_command_error(self, ctx, exception):
		logging.error("Command failed with {0} error: {1}".format(type(exception), exception))

		if isinstance(exception, commands.MissingAnyRole):
			await ctx.send("You aren't cool enough to use this command.")
