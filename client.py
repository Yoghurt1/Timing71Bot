#!/usr/bin/env python
import nest_asyncio
nest_asyncio.apply()

import requests
import asyncio
import json
import datetime
import asyncio
import discordClient
import os
import sys
import time
import logging
from autobahn.wamp.types import SubscribeOptions
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from lzstring import LZString
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from helpers import msgFormat
from discord_config import Settings
from functools import partial

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
	_manifest = ""

	async def onJoin(self, details):
		await self.fetchEvents()

		def startClient():
			client = discordClient.DiscordClient(self)
			client.run(TOKEN)

		loop = asyncio.get_event_loop()
		loop.run_in_executor(self._executor, startClient())

	async def fetchEvents(self):
		def onEventsFetched(i):
			self._events = i["payload"]

		self.subscribe(onEventsFetched, "livetiming.directory", options=SubscribeOptions(get_retained=True))
	
	async def events(self):
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
			return None

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
		
	async def getCarDetails(self, ctx, carNum, spec=None):
		async def sendToDiscord(ctx, message):
			await ctx.send(msgFormat.formatCarInfo(message, spec, self._currentEvent))

		res = await self.call("livetiming.service.requestState." + self._currentEvent["uuid"])
		for car in res["cars"]:
			if car[0] == str(carNum):
				specList = []
				for col in self._currentEvent["colSpec"]:
					try:
						specList.append(col[2])
					except IndexError:
						specList.append(col[0])

				carList = [i for i in car]

				carDict = dict(zip(specList, carList))
				return await sendToDiscord(ctx, carDict)
		
		return await sendToDiscord(ctx, "Couldn't find a car with that number.")

	def unbind(self):
		os.execv(__file__, sys.argv)

	def onDisconnect(self):
		asyncio.get_event_loop().stop()

if __name__ == '__main__':
	url = getRelay()
	realm = "timing"

	runner = ApplicationRunner(url, realm)
	runner.run(Component)
