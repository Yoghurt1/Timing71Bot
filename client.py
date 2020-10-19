import requests
import asyncio
import json
import datetime
import discord
import asyncio
import nest_asyncio
from enum import Enum
from autobahn.wamp.types import SubscribeOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from lzstring import LZString
from threading import Thread

nest_asyncio.apply()

# def getBestRelay(relays):
#     clients = 1000
#     bestRelay = ""
#     for key, value in relays.items():
#         print(value[0])
#         print(clients)
#         if value[0] < clients:
#             clients = value
#             bestRelay = key

class MessageClass(Enum):
	INITIALISE_DIRECTORY = 1
	SERVICE_REGISTRATION = 2
	SERVICE_DEREGISTRATION = 3
	SERVICE_DATA = 4
	DIRECTORY_LISTING = 5
	SCHEDULE_LISTING = 6
	ANALYSIS_DATA = 7
	SERVICE_DATA_COMPRESSED = 8
	ANALYSIS_DATA_COMPRESSED = 9
	RECORDING_LISTING = 10

def getRelay():
	getRelays = requests.get("https://www.timing71.org/relays")
	relays = getRelays.json()['args'][0]
	return list(relays.keys())[0]

class DiscordClient(discord.Client):
	async def on_ready(self):
		print('We have logged in as {0.user}'.format(self))

	async def on_message(self, message):
		if message.author == self.user:
			return

		if message.content.startswith('$hello'):
			await message.channel.send('Hello!')

class Component(ApplicationSession):
	_TOKEN = "NzY2NzE4Mjc1NDY3MjE0OTQw.X4ncCQ.0h147vr2XBQE9Xpz05tkmOIdDgs"

	async def onJoin(self, details):
		self.client = DiscordClient()
		
		# print("start")
		# loop = asyncio.new_event_loop()
		# loop.create_task(self.client.start(self._TOKEN))
		# asyncio.set_event_loop(loop)
		# loop.run_forever()
		# print("fin")

		self.currentEvents = await self.fetchEvents()
		if self.currentEvents == []:
			print("No events currently ongoing. Exiting.")
			self.leave()
		else:
			self.selectedEvent = await self.menu(self.currentEvents)
			await self.subscribeToEvent(self.selectedEvent)

	async def fetchEvents(self):
		try:
			res = await self.call("livetiming.directory.listServices")
		except Exception as e:
			print("Fucked", e)
		else:
			return res
	
	async def menu(self, events):
		print("Pick event:")
		for idx, event in enumerate(events):
			print(str(idx + 1) + ". " + event["name"] + " - " + event["description"])
		
		menuSelect = int(input("Selection: ")) - 1
		selection = self.currentEvents[menuSelect]
		return selection

	async def subscribeToEvent(self, event):
		print("Subscribing to " + event)

		def onTimingEvent(i):
			pl = i["payload"]
			decompressed = LZString().decompressFromUTF16(pl)
			res = json.loads(decompressed)

		def onNewTrackMessage(i):
			print("[TRACK EVENT]")
			print(i)

		def onNewCarMessage(i):
			print("[CAR EVENT]")
			pl = i["payload"]
			carNum = next(iter(pl))
			print(pl[carNum][-1])

		await self.subscribe(onTimingEvent, "livetiming.service." + event["uuid"])
		await self.subscribe(onNewTrackMessage, "livetiming.analysis/" + event["uuid"] + "/messages", options=SubscribeOptions(get_retained=True))
		await self.subscribe(onNewCarMessage, "livetiming.analysis/" + event["uuid"] + "/car_messages", options=SubscribeOptions(match="prefix"))
		await self.subscribe(onNewCarMessage, "livetiming.analysis/" + event["uuid"] + "/stint", options=SubscribeOptions(match="prefix"))

	def onDisconnect(self):
		asyncio.get_event_loop().stop()

if __name__ == '__main__':
	url = getRelay()
	realm = "timing"

	runner = ApplicationRunner(url, realm)
	runner.run(Component)
