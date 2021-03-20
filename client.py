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
import discord
from autobahn.wamp.types import SubscribeOptions, ComponentConfig
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from autobahn.asyncio.component import Component, run
from lzstring import LZString
from concurrent.futures import ThreadPoolExecutor
from helpers import msgFormat
from discord_config import Settings

def getRelay():
	getRelays = requests.get("https://www.timing71.org/relays")
	relays = getRelays.json()['args'][0]
	return list(relays.keys())[0]

TOKEN = os.environ["DISCORD_TOKEN"]

NUM_REACTS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

class TimingSession(ApplicationSession):
	_events = []
	_currentEvent = []
	_status = ""
	_config = Settings(defaults={
			"adminRole": "Admin",
			"modRole": "Tiddy Boiz",
			"delay": 0
		},
		filename="config.json"
	)
	_executor = ThreadPoolExecutor(2)
	_manifest = ""
	_client = None

	async def onJoin(self, details):
		def startClient():
			self._client = discordClient.DiscordClient(self)
			self._client.run(TOKEN)

		loop = asyncio.get_event_loop()
		loop.run_in_executor(self._executor, startClient())

	async def sendEventMsg(self, channel, msg, currentEvents):
		msg = await channel.send(msg)

		for i in range(len(currentEvents)):
			await msg.add_reaction(NUM_REACTS[i])

		while True:
			updatedMsg = await channel.fetch_message(msg.id)
			for idx, react in enumerate(updatedMsg.reactions):
				if react.count >= 5:
					await channel.send("React threshold reached for event number {0}, connecting.".format(idx + 1))
					return await self.connectToEvent(str(idx + 1), channel)
			
			await asyncio.sleep(1)

		

	async def fetchEvents(self):
		def onEventsFetched(i):
			if i["payload"] != [] and self._events != i["payload"]:
				self._events = i["payload"]
				currentEvents = []
				loop = asyncio.get_event_loop()

				for idx, event in enumerate(self._events):
					currentEvents.append(str(idx + 1) + ". " + event["name"] + " - " + event["description"])

				msg = "New event(s) started:\n"
				msg = msg + "\n".join(currentEvents) + "\nUse the reacts below for each event number if you want to connect."
				channel = self._client.get_channel(295518694694453248)

				asyncio.run_coroutine_threadsafe(self.sendEventMsg(channel, msg, currentEvents), loop)

		self.subscribe(onEventsFetched, "livetiming.directory", options=SubscribeOptions(get_retained=True))
	
	def events(self):
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

			activity = discord.Activity(type=discord.ActivityType.watching, name=event["name"] + " - " + event["description"])
			await self._client.change_presence(activity=activity)
			
		else:
			return None

		async def sendToDiscord(ctx, message):
			try:
				await asyncio.sleep(int(self._config.delay))
				logging.info("Sending message:")
				logging.info(message)
				await ctx.send(message)
			except Exception as e:
				logging.error("Failed to send message to Discord:")
				logging.error(e)

		def onNewTrackMessage(i):
			logging.info("[TRACK EVENT]")
			
			msg = i["payload"]["messages"][0]
			logging.info(msg)

			asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatTrackMessage(msg)), loop)

			if any(x in msg[2].lower() for x in ["chequered flag", "checkered flag"]):
				self._config.set("delay", "0")
				asyncio.run_coroutine_threadsafe(self._client.change_presence(), loop)
				carSub.unsubscribe()
				trackSub.unsubscribe()
				pitSub.unsubscribe()

		def onNewCarMessage(i):
			logging.info("[CAR EVENT]")
			
			payload = i["payload"]
			carNum = next(iter(payload))
			msg = payload[carNum][-1]

			logging.info(msg)

			if msg[3] not in ["pb", None]:
				asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatCarMessage(msg)), loop)
		
		def onNewPitMessage(i):
			logging.info("[PIT EVENT]")

		carSub = self.subscribe(onNewCarMessage, "livetiming.analysis/" + event["uuid"] + "/car_messages", options=SubscribeOptions(match="prefix"))
		trackSub = self.subscribe(onNewTrackMessage, "livetiming.analysis/" + event["uuid"] + "/messages")
		pitSub = self.subscribe(onNewPitMessage, "livetiming.analysis/" + event["uuid"] + "/stint", options=SubscribeOptions(match="prefix"))
	
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
		asyncio.get_event_loop().close()

if __name__ == '__main__':
	component = Component(
		session_factory=TimingSession,
		transports=getRelay(),
		realm="timing"
	)

	run([component])
