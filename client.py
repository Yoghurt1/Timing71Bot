#!/usr/bin/env python
import requests
import asyncio
import json
import datetime
import asyncio
import nest_asyncio
import discordClient
import queue
import os
import sys
import time
from enum import Enum
from autobahn.wamp.types import SubscribeOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from lzstring import LZString
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from helpers import msgFormat

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

TOKEN = os.environ["DISCORD_TOKEN"]

class Component(ApplicationSession):
	_events = []
	_currentEvent = []

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
	
	def getCurrentEvent(self):
		return self._currentEvent

	async def refreshEvents(self):
		self._events = await self.fetchEvents()
	
	def menu(self):
		loop = asyncio.new_event_loop()
		asyncio.run_coroutine_threadsafe(self.refreshEvents(), loop)
		
		currentEvents = []
		if self._events == []:
			return "No events currently ongoing."
		
		for idx, event in enumerate(self._events):
			currentEvents.append(str(idx + 1) + ". " + event["name"] + " - " + event["description"])
		
		return "\n".join(currentEvents)

	async def connectToEvent(self, eventNum, ctx):
		loop = asyncio.get_event_loop()

		if len(eventNum) == 1:
			eventNum = int(eventNum) - 1
			event = self._events[eventNum]

			self._currentEvent = event

			print("Subscribing to " + event["uuid"])
		else:
			self._currentEvent = {"uuid": eventNum, "name": "Secret event", "description": "Shhhh"}
			event = self._currentEvent

		async def sendToDiscord(ctx, message):
			await ctx.send(message)

		def onNewTrackMessage(i):
			print("[TRACK EVENT]")
			msg = i["payload"]["messages"][0]
			print(msg)
			if "Chequered flag" in msg[2]:
				asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatTrackMessage(msg)), loop)
				time.sleep(2)
				asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatTrackMessage("Event finished, unbinding.")), loop)
				self.unbind()

			asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatTrackMessage(msg)), loop)

		def onNewCarMessage(i):
			print("[CAR EVENT]")
			pl = i["payload"]
			carNum = next(iter(pl))
			msg = pl[carNum][-1]
			print(msg)
			if msg[3] not in ['pb', None]:
				asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatCarMessage(msg)), loop)
		
		def onNewPitMessage(i):
			print("[PIT EVENT]")

		self.subscribe(onNewCarMessage, "livetiming.analysis/" + event["uuid"] + "/car_messages", options=SubscribeOptions(match="prefix"))
		self.subscribe(onNewTrackMessage, "livetiming.analysis/" + event["uuid"] + "/messages")
		self.subscribe(onNewPitMessage, "livetiming.analysis/" + event["uuid"] + "/stint", options=SubscribeOptions(match="prefix"))
	
	def formatCarMessage(self, msg):
		if msg[1] == '':
			return msgFormat.formatWithFlags(msg[2], self._currentEvent)
		else:
			cleanMsg = msg[1] + " - " + msg[2]

			return msgFormat.formatWithFlags(cleanMsg, self._currentEvent)

	def formatTrackMessage(self, msg):
		cleanMsg = msg[1] + " - " + msg[2]

		return msgFormat.formatWithFlags(cleanMsg, self._currentEvent)
		
	async def getCarDetails(self, carNum):
		res = await self.call("livetiming.service.requestState." + self._currentEvent["uuid"])
		return res

	def unbind(self):
		os.execv(__file__, sys.argv)

	def onDisconnect(self):
		asyncio.get_event_loop().stop()

if __name__ == '__main__':
	url = getRelay()
	realm = "timing"

	runner = ApplicationRunner(url, realm)
	runner.run(Component)
