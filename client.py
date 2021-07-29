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
TIMEOUT = 300
NUM_REACTS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

class TimingSession(ApplicationSession):
	_events = []
	_currentEvent = []
	_status = ""
	_config = Settings(defaults={
			"adminRole": "Admin",
			"modRole": "Tiddy Boiz",
			"delay": 0,
			"excludes": []
		},
		filename="config.json"
	)
	_executor = ThreadPoolExecutor(2)
	_manifest = ""
	_client = None
	_carSub = None
	_trackSub = None
	_pitSub = None
	_carDetails = None
	_lastTimestamp = 0.0

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

		timer = time.time()

		while time.time() < timer + TIMEOUT:
			try:
				updatedMsg = await channel.fetch_message(msg.id)
			except Exception:
				return
			for idx, react in enumerate(updatedMsg.reactions):
				if react.count >= 5:
					await channel.send("React threshold reached for event number {0}, connecting.".format(idx + 1))
					await updatedMsg.delete()
					return await self.connectToEvent(str(idx + 1), channel)
			
			await asyncio.sleep(1)

		return await msg.delete()

	async def fetchEvents(self):
		def onEventsFetched(i):
			if i["payload"] != [] and self._events != i["payload"]:
				self._events = i["payload"]
				currentEvents = []
				loop = asyncio.get_event_loop()

				for idx, event in enumerate(self._events):
					currentEvents.append(str(idx + 1) + ". " + event["name"] + " - " + event["description"])

				if self._currentEvent not in i["payload"]:
					msg = "New event(s) started:\n"
					msg = msg + "\n".join(currentEvents) + "\nUse the reacts below for each event number if you want to connect."
					channel = self._client.get_channel(767481691529805846)

					asyncio.run_coroutine_threadsafe(self.sendEventMsg(channel, msg, currentEvents), loop)

		self.subscribe(onEventsFetched, "livetiming.directory", options=SubscribeOptions(get_retained=True))
	
	def events(self):
		currentEvents = []
		if self._events == []:
			return "No events currently ongoing."
		
		for idx, event in enumerate(self._events):
			currentEvents.append(str(idx + 1) + ". " + event["name"] + " - " + event["description"])
		
		return "\n".join(currentEvents)

	async def closeEvent(self):
		await self._client.change_presence()
		self._lastTimestamp = 0

		if self._carSub != None:
			subs = asyncio.gather(
				self._carSub.result().unsubscribe(),
				self._trackSub.result().unsubscribe(),
				self._pitSub.result().unsubscribe()
			)

			logging.info("Unsubscribed from event {0}".format(self._currentEvent["uuid"]))

		self._currentEvent = []

	async def connectToEvent(self, eventNum, ctx):
		loop = asyncio.get_event_loop()
		self._lastTimestamp = time.time()
		logging.info("Timestamp: {0}".format(self._lastTimestamp))

		if self._currentEvent != []:
			await self.closeEvent()

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

			logging.info(i["payload"]["messages"])
			logging.info("Original timestamp: {0}".format(self._lastTimestamp))

			for msg in reversed(i["payload"]["messages"]):
				logging.info(msg)
				if float(msg[0]) > float(self._lastTimestamp):
					asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatTrackMessage(msg)), loop)
			
			self._lastTimestamp = i["payload"]["messages"][0][0]
			logging.info("Final timestamp: {0}".format(self._lastTimestamp))

		def onNewCarMessage(i):
			def shouldSendMsg(msg):
				if any(x in msg[2].lower() for x in ["running slowly or stopped", "has resumed"]):
					if any(x in self._currentEvent["description"] for x in ["practice", "qualifying"]):
						return False
				elif msg[3] in ["pb", None]:
					return False
				elif any(x in msg[2].lower() for x in self._config.excludes):
					return False
				else:
					return True

			logging.info("[CAR EVENT]")
			
			payload = i["payload"]
			carNum = next(iter(payload))
			msg = payload[carNum][-1]

			logging.info(msg)

			if shouldSendMsg(msg):
				if "indycar" in self._currentEvent["name"].lower() and msg[3] == "sb":
					carDetailsFut = asyncio.run_coroutine_threadsafe(self._getCarDetailsInt(msg[4], "last lap speed"), loop)
					carDetailsFut.add_done_callback(lambda fut: asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatCarMessage(msg, self._carDetails)), loop))
				else:
					asyncio.run_coroutine_threadsafe(sendToDiscord(ctx, self.formatCarMessage(msg)), loop)
		
		def onNewPitMessage(i):
			logging.info("[PIT EVENT]")

		self._carSub = self.subscribe(onNewCarMessage, "livetiming.analysis/" + event["uuid"] + "/car_messages", options=SubscribeOptions(match="prefix"))
		self._trackSub = self.subscribe(onNewTrackMessage, "livetiming.analysis/" + event["uuid"] + "/messages")
		self._pitSub = self.subscribe(onNewPitMessage, "livetiming.analysis/" + event["uuid"] + "/stint", options=SubscribeOptions(match="prefix"))
	
	def formatCarMessage(self, msg, extraDetails=None):
		if msg[1] == '':
			return msgFormat.formatWithFlags(msg[2], self._currentEvent)
		else:
			if extraDetails != None:
				cleanMsg = msg[1] + " - " + msg[2] + " / " + extraDetails.split(" ")[-1]
			else:
				cleanMsg = msg[1] + " - " + msg[2]

			return msgFormat.formatWithFlags(cleanMsg, self._currentEvent)

	def formatTrackMessage(self, msg):
		cleanMsg = msg[1] + " - " + msg[2]

		return msgFormat.formatWithFlags(cleanMsg, self._currentEvent)

	async def _getCarDetailsInt(self, carNum, spec=None):
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
				self._carDetails = msgFormat.formatCarInfo(carDict, spec, self._currentEvent)
		
	async def getCarDetails(self, ctx, carNum, spec=None):
		async def sendToDiscord(ctx, message):
			await ctx.send(message)

		try:
			await self._getCarDetailsInt(carNum, spec)
			return await sendToDiscord(ctx, self._carDetails)
		except:
			return await sendToDiscord(ctx, "Couldn't find a car with that number.")

	async def getTrackInfo(self, ctx):
		async def sendToDiscord(ctx, message):
			await ctx.send(msgFormat.formatTrackInfo(message, self._currentEvent))

		print(self._currentEvent["trackDataSpec"])
		res = await self.call("livetiming.service.requestState.{0}".format(self._currentEvent["uuid"]))
		trackDict = dict(zip(self._currentEvent["trackDataSpec"], res["session"]["trackData"]))
		await sendToDiscord(ctx, trackDict)
	
	def setDelay(self, delay):
		self._config.set("delay", delay)
		self._config.save()

	def getDelay(self):
		return self._config.delay

	def addExclude(self, exclude):
		newExcludes = self._config.excludes + [exclude]
		self._config.set("excludes", newExcludes)
		self._config.save()
	
	def getExcludes(self):
		return self._config.excludes

	def clearExcludes(self):
		self._config.set("excludes", [])
		self._config.save()

	def onDisconnect(self):
		asyncio.get_event_loop().close()

if __name__ == '__main__':
	component = Component(
		session_factory=TimingSession,
		transports=getRelay(),
		realm="timing"
	)

	run([component])
