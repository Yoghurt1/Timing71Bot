#!/usr/bin/env python
import requests
import asyncio
import json
import datetime
import asyncio
import nest_asyncio
import discordClient
import os
import sys
import time
import logging
from enum import Enum
from autobahn.wamp.types import SubscribeOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from lzstring import LZString
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from helpers import msgFormat
from discord_config import Settings
from functools import partial

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
	_status = ""
	_config = Settings(defaults={
			"adminRole": "Admin",
			"modRole": "Tiddy Boiz",
			"delay": 0
		},
		filename="config.json",
	)
	_executor = ThreadPoolExecutor(2)
	_state = ""

	async def onJoin(self, details):
		def startClient():
			loop = asyncio.new_event_loop()
			asyncio.set_event_loop(loop)
			
			client = discordClient.DiscordClient(self)
			
			ret = loop.run_until_complete(client.start(TOKEN))
			loop.close()
			return ret

		self._executor.submit(startClient)

		await self.fetchEvents()

	async def fetchEvents(self):
		try:
			res = await self.call("livetiming.directory.listServices")
		except Exception as e:
			logging.error("Failed to fetch events: {0}".format(e))
			return None
		else:
			logging.info("Updating events: {0}".format(res))
			self._events = res
	
	async def events(self, loop):
		asyncio.run_coroutine_threadsafe(self.fetchEvents(), loop)

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

			logging.info("Subscribing to " + event["uuid"])
		else:
			self._currentEvent = {"uuid": eventNum, "name": "Secret event", "description": "Shhhh"}
			event = self._currentEvent

		async def sendToDiscord(ctx, message):
			await asyncio.sleep(int(self._config.delay))
			await ctx.send(message)

		def onNewTrackMessage(i):
			logging.info("[TRACK EVENT]")
			
			msg = i["payload"]["messages"][0]
			logging.info(msg)

			asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatTrackMessage(msg)), loop)

			if "Chequered flag" in msg[2]:
				self._config.set("delay", "0")

		def onNewCarMessage(i):
			logging.info("[CAR EVENT]")
			
			payload = i["payload"]
			carNum = next(iter(payload))
			msg = payload[carNum][-1]

			logging.info(msg)

			if msg[3] not in ['pb', None]:
				asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatCarMessage(msg)), loop)
		
		def onNewPitMessage(i):
			logging.info("[PIT EVENT]")

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
		
	async def getCarDetails(self, carNum, ctx):
		async def sendToDiscord(ctx, message):
			await ctx.send(message)

		res = await self.call("livetiming.service.requestState." + self._currentEvent["uuid"])
		logging.debug(res)
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
