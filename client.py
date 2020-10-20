import requests
import asyncio
import json
import datetime
import asyncio
import nest_asyncio
import discordClient
from os import environ
from enum import Enum
from autobahn.wamp.types import SubscribeOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from lzstring import LZString
from threading import Thread
from concurrent.futures import ThreadPoolExecutor

nest_asyncio.apply()

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

TOKEN = environ["DISCORD_TOKEN"]

class Component(ApplicationSession):
	async def onJoin(self, details):
		def startClient():
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
			
			client = discordClient.DiscordClient(self)
			
			ret = loop.run_until_complete(client.start(TOKEN))
			loop.close()
			return ret

		executor = ThreadPoolExecutor(2)
		executor.submit(startClient)

	async def fetchEvents(self):
		try:
			res = await self.call("livetiming.directory.listServices")
		except Exception as e:
			print("Failed to fetch events: ", e)
			return None
		else:
			return res
	
	async def menu(self, events):
		for idx, event in enumerate(events):
			events.append(str(idx + 1) + ". " + event["name"] + " - " + event["description"])
		
		if events == []:
			return "No events currently ongoing."
		return "\n".join(events)

	async def subscribeToEvent(self, event):
		print("Subscribing to " + event)

		def onTimingEvent(i):
			pl = i["payload"]
			decompressed = LZString().decompressFromUTF16(pl)
			res = json.loads(decompressed)

		def onNewTrackMessage(i):
			print("[TRACK EVENT]")
			print(i)
			return i

		def onNewCarMessage(i):
			print("[CAR EVENT]")
			pl = i["payload"]
			carNum = next(iter(pl))
			print(pl[carNum][-1])
			return pl[carNum][-1]

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
