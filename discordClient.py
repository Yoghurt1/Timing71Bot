import discord

class DiscordClient(discord.Client):
	async def on_ready(self):
		print('We have logged in as {0.user}'.format(self))

	async def on_message(self, message):
		if message.author == self.user:
			return

		if message.content.startswith("!events"):
			await message.channel.send(await self.timingClient.menu(self.timingClient.currentEvents))

	def __init__(self, timingClient):
		self.timingClient = timingClient
		super().__init__()