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
    relays = getRelays.json()["args"][0]
    return list(relays.keys())[0]


TOKEN = os.environ["DISCORD_TOKEN"]
TIMEOUT = 300
NUM_REACTS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
ECS_ID = 295518694694453248


class TimingSession(ApplicationSession):
    _events = []
    _currentEvent = []
    _status = ""
    _config = Settings(
        defaults={
            "adminRole": "Admin",
            "modRole": "Tiddy Boiz",
            "delay": 0,
            "excludes": [],
        },
        filename="config.json",
    )
    _executor = ThreadPoolExecutor(2)
    _manifest = ""
    _client: discordClient.DiscordClient = None
    _carSub = None
    _trackSub = None
    _pitSub = None
    _carDetails = None
    _lastTimestamp = 0.0
    _activeThread: discord.Thread = None

    async def onJoin(self, details):
        def startClient():
            self._client = discordClient.DiscordClient(self)
            self._client.run(TOKEN)

        loop = asyncio.get_event_loop()
        loop.run_in_executor(self._executor, startClient())

    async def sendEventMsg(self, channel, msg, currentEvents):
        msg = await channel.send(msg)

        for eventNum in range(len(currentEvents)):
            await msg.add_reaction(NUM_REACTS[eventNum])

        timer = time.time()

        while time.time() < timer + TIMEOUT:
            try:
                updatedMsg = await channel.fetch_message(msg.id)
            except Exception:
                return
            for idx, react in enumerate(updatedMsg.reactions):
                if react.count >= 5:
                    await channel.send(
                        "React threshold reached for event number {0}, connecting in new thread.".format(
                            idx + 1
                        )
                    )

                    await updatedMsg.delete()
                    return await self.connectToEvent(str(idx + 1), channel)

            await asyncio.sleep(1)

        return await msg.delete()

    async def fetchEvents(self):
        def onEventsFetched(newMsg):
            loop = asyncio.get_event_loop()

            if newMsg["payload"] != [] and self._events != newMsg["payload"]:
                self._events = newMsg["payload"]

                if (
                    self._currentEvent not in self._events
                    and self._activeThread != None
                ):
                    asyncio.run_coroutine_threadsafe(
                        self._activeThread.edit(archived=True), loop
                    )

                currentEvents = []

                for index, event in enumerate(self._events):
                    currentEvents.append(msgFormat.formatEventMessage(index, event))

                if self._currentEvent not in newMsg["payload"]:
                    msg = "New event(s) started:\n"
                    msg = (
                        msg
                        + "\n".join(currentEvents)
                        + "\nUse the reacts below for each event number if you want to connect."
                    )
                    channel = self._client.get_channel(ECS_ID)

                    asyncio.run_coroutine_threadsafe(
                        self.sendEventMsg(channel, msg, currentEvents), loop
                    )

        self.subscribe(
            onEventsFetched,
            "livetiming.directory",
            options=SubscribeOptions(get_retained=True),
        )

    def events(self):
        currentEvents = []

        if self._events == []:
            return "No events currently ongoing."

        for index, event in enumerate(self._events):
            currentEvents.append(msgFormat.formatEventMessage(index, event))

        return "\n".join(currentEvents)

    async def closeEvent(self):
        await self._client.change_presence()
        self._lastTimestamp = 0

        if self._carSub != None:
            asyncio.gather(
                self._carSub.result().unsubscribe(),
                self._trackSub.result().unsubscribe(),
                self._pitSub.result().unsubscribe(),
            )

            logging.info(
                "Unsubscribed from event {0}".format(self._currentEvent["uuid"])
            )

        await self._activeThread.edit(archived=True)

        self._currentEvent = []

    async def connectToEvent(self, eventNum, ctx):
        loop = asyncio.get_event_loop()

        self._lastTimestamp = time.time()
        logging.info("Timestamp: {0}".format(self._lastTimestamp))

        if self._currentEvent != []:
            await self.closeEvent()

        eventNum = int(eventNum) - 1
        self._currentEvent = self._events[eventNum]

        logging.info("Subscribing to " + self._currentEvent["uuid"])

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name=self._currentEvent["name"] + " - " + self._currentEvent["description"],
        )

        await self._client.change_presence(activity=activity)

        threadName = "{name} - {description} | Timing".format(
            name=self._currentEvent["name"],
            description=self._currentEvent["description"],
        )

        self._activeThread = await ctx.create_thread(name=threadName)

        async def sendToDiscord(message):
            try:
                await asyncio.sleep(int(self._config.delay))
                logging.info("Sending message:")
                logging.info(message)
                await self._activeThread.send(message)
            except Exception as e:
                logging.error("Failed to send message to Discord:")
                logging.error(e)

        def onNewTrackMessage(newMsg):
            logging.info("[TRACK EVENT]")

            logging.info(newMsg["payload"]["messages"])
            logging.info("Original timestamp: {0}".format(self._lastTimestamp))

            for msg in reversed(newMsg["payload"]["messages"]):
                logging.info(msg)
                if float(msg[0]) > float(self._lastTimestamp):
                    asyncio.run_coroutine_threadsafe(
                        sendToDiscord(self.formatTrackMessage(msg)), loop
                    )

            self._lastTimestamp = newMsg["payload"]["messages"][0][0]
            logging.info("Final timestamp: {0}".format(self._lastTimestamp))

        def onNewCarMessage(newMsg):
            def shouldSendMsg(msg):
                if any(
                    x in msg[2].lower()
                    for x in ["running slowly or stopped", "has resumed"]
                ):
                    if any(
                        x in self._currentEvent["description"].lower()
                        for x in ["practice", "qualifying"]
                    ):
                        return False
                elif msg[3] in ["pb", None]:
                    return False
                elif any(x in msg[2].lower() for x in self._config.excludes):
                    return False
                else:
                    return True

            logging.info("[CAR EVENT]")

            payload = newMsg["payload"]
            carNum = next(iter(payload))
            msg = payload[carNum][-1]

            logging.info(msg)

            if shouldSendMsg(msg):
                if "indycar" in self._currentEvent["name"].lower() and msg[3] == "sb":
                    carDetailsFut = asyncio.run_coroutine_threadsafe(
                        self.fetchCarState(msg[4], "last lap speed"), loop
                    )
                    carDetailsFut.add_done_callback(
                        lambda fut: asyncio.run_coroutine_threadsafe(
                            sendToDiscord(self.formatCarMessage(msg, self._carDetails)),
                            loop,
                        )
                    )
                else:
                    asyncio.run_coroutine_threadsafe(
                        sendToDiscord(self.formatCarMessage(msg)), loop
                    )

        def onNewPitMessage(i):
            logging.info("[PIT EVENT]")

        self._carSub = self.subscribe(
            onNewCarMessage,
            "livetiming.analysis/" + self._currentEvent["uuid"] + "/car_messages",
            options=SubscribeOptions(match="prefix"),
        )

        self._trackSub = self.subscribe(
            onNewTrackMessage,
            "livetiming.analysis/" + self._currentEvent["uuid"] + "/messages",
        )

        self._pitSub = self.subscribe(
            onNewPitMessage,
            "livetiming.analysis/" + self._currentEvent["uuid"] + "/stint",
            options=SubscribeOptions(match="prefix"),
        )

    def formatCarMessage(self, msg, extraDetails=None):
        if msg[1] == "":
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

    async def fetchCarState(self, carNum, spec=None):
        res = await self.call(
            "livetiming.service.requestState." + self._currentEvent["uuid"]
        )
        for car in res["cars"]:
            if car[0] == str(carNum):
                specList = []
                for col in self._currentEvent["colSpec"]:
                    try:
                        specList.append(col[2])
                    except IndexError:
                        specList.append(col[0])

                carList = [i for i in car]

                self._carDetails = dict(zip(specList, carList))

    async def getCarDetails(self, ctx, carNum, spec=None):
        async def sendToDiscord(ctx, message):
            await ctx.send(
                ".car {carNum} called by {author}".format(
                    carNum=carNum, author=ctx.author
                )
            )
            await ctx.send(message)

        try:
            await self.fetchCarState(carNum, spec)
            return await sendToDiscord(
                ctx, msgFormat.formatCarInfo(self._carDetails, spec, self._currentEvent)
            )
        except:
            return await sendToDiscord(
                ctx,
                "An error occurred. Check you've entered a valid car number, moron.",
            )

    async def whoIsCar(self, ctx, carNum):
        async def sendToDiscord(ctx, message):
            await ctx.send(
                ".whois {carNum} called by {author}".format(
                    carNum=carNum, author=ctx.author
                )
            )
            await ctx.send(message)

        try:
            await self.fetchCarState(carNum)
            whoIsDict = dict(
                filter(
                    lambda elem: any(
                        x in elem[0].lower()
                        for x in [
                            "car number",
                            "class",
                            "team",
                            "driver",
                            "car",
                            "position",
                        ]
                    ),
                    self._carDetails.items(),
                )
            )

            return await sendToDiscord(
                ctx, msgFormat.formatCarInfo(whoIsDict, None, self._currentEvent)
            )
        except Exception as e:
            logging.info(e)
            return await sendToDiscord(
                ctx,
                "An error occurred. Check you've entered a valid car number, moron.",
            )

    async def getTrackInfo(self, ctx):
        async def sendToDiscord(ctx, message):
            if isinstance(message, str):
                return await ctx.send(message)

            return await ctx.send(
                msgFormat.formatTrackInfo(message, self._currentEvent)
            )

        if self._currentEvent["trackDataSpec"] == []:
            return await sendToDiscord(ctx, "No track data for this session.")

        res = await self.call(
            "livetiming.service.requestState.{0}".format(self._currentEvent["uuid"])
        )

        trackDict = dict(
            zip(self._currentEvent["trackDataSpec"], res["session"]["trackData"])
        )

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


if __name__ == "__main__":
    component = Component(
        session_factory=TimingSession, transports=getRelay(), realm="timing"
    )

    run([component])
