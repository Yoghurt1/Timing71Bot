import requests
import asyncio
import json
import datetime
import asyncio
import nest_asyncio
import discordClient
import queue
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

class FlagStatus(Enum):
	CAUTION = 9
	CHEQUERED = 3
	CODE_60 = 6
	CODE_60_ZONE = 12
	FCY = 5
	GREEN = 1
	NONE = 0
	RED = 10
	SC = 8
	SLOW_ZONE = 11
	VSC = 7
	WHITE = 2
	YELLOW = 4

def getRelay():
	getRelays = requests.get("https://www.timing71.org/relays")
	relays = getRelays.json()['args'][0]
	return list(relays.keys())[0]

TOKEN = environ["DISCORD_TOKEN"]

class Component(ApplicationSession):
	_events = []
	_currentEvent = ""

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

		self._events = await self.fetchEvents()
		self.msgQueue = queue.Queue()

	async def fetchEvents(self):
		try:
			res = await self.call("livetiming.directory.listServices")
		except Exception as e:
			print("Failed to fetch events: ", e)
			return None
		else:
			return res

	async def fetchRecordings(self):
		try:
			res = await self.call("livetiming.directory.listRecordings")
		except Exception as e:
			print("Failed to fetch recordings: ", e)
			return None
		else:
			return res

	def refreshEvents(self):
		self._events = yield self.fetchEvents()
		return
	
	def getCurrentEvent(self):
		return self._currentEvent

	def getRecordings(self):
		res = yield self.fetchRecordings()
		return res
	
	async def menu(self):
		self.refreshEvents()
		currentEvents = []
		if self._events == []:
			return "No events currently ongoing."
		
		for idx, event in enumerate(self._events):
			currentEvents.append(str(idx + 1) + ". " + event["name"] + " - " + event["description"])
		
		return "\n".join(currentEvents)

	async def connectToEvent(self, eventNum, ctx):
		loop = asyncio.get_event_loop()

		self.refreshEvents()

		eventNum = int(eventNum) - 1
		event = self._events[eventNum]

		self._currentEvent = event["name"] + " - " + event["description"]

		print("Subscribing to " + event["uuid"])

		async def sendToDiscord(ctx, message):
			await ctx.send(message)

		def onNewTrackMessage(i):
			print("[TRACK EVENT]")
			print(i)
			send = asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, str(i)), loop)
			print(send.result())

		def onNewCarMessage(i):
			print("[CAR EVENT]")
			pl = i["payload"]
			carNum = next(iter(pl))
			msg = pl[carNum][-1]
			print(msg)
			# if msg[3] in ['sb', 'raceControl']:
			send = asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatCarMessage(msg)), loop)
			print(send.result())
		
		def onNewPitMessage(i):
			print("[PIT EVENT]")
			print(i)

		print("start subs")
		# await self.subscribe(onTimingEvent, "livetiming.service." + event["uuid"])
		self.subscribe(onNewCarMessage, "livetiming.analysis/" + event["uuid"] + "/car_messages", options=SubscribeOptions(match="prefix"))
		print("car messages")
		self.subscribe(onNewTrackMessage, "livetiming.analysis/" + event["uuid"] + "/messages", options=SubscribeOptions(get_retained=True))
		print("messages")
		self.subscribe(onNewPitMessage, "livetiming.analysis/" + event["uuid"] + "/stint", options=SubscribeOptions(match="prefix"))

		print("subscribes complete")
	
	def formatCarMessage(self, msg):
		if msg[1] == '':
			return msg[2]
		else:
			return (msg[1] + " - " + msg[2])

	def onDisconnect(self):
		asyncio.get_event_loop().stop()

if __name__ == '__main__':
	url = getRelay()
	realm = "timing"

	runner = ApplicationRunner(url, realm)
	runner.run(Component)
