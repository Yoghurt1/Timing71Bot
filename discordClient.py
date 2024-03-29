import logging
from discord.ext import commands
import discord


class DiscordClient(commands.Bot):
    _commands = ()

    async def on_ready(self):
        logging.info("We have logged in as {0.user}".format(self))
        await self.timingClient.fetchEvents()

        await self.load_extension("cogs.timingCog")
        await self.load_extension("cogs.managementCog")
        await self.load_extension("cogs.memeCog")

    def __init__(self, timingClient):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=".", intents=intents)

        self.timingClient = timingClient

        _commands = tuple([".{0}".format(i) for i in self.commands])

    async def on_command_error(self, ctx, exception):
        logging.error(
            "Command failed with {0} error: {1}".format(type(exception), exception)
        )

        if isinstance(exception, commands.MissingAnyRole):
            await ctx.send("You aren't cool enough to use this command.")
        elif isinstance(exception, commands.CommandOnCooldown):
            await ctx.send("Have some patience, child. {0}.".format(exception))
        elif isinstance(exception, commands.CommandInvokeError):
            await ctx.send("Unknown error occurred. Good job, idiot.")

    async def on_message(self, message: discord.Message):
        if (
            isinstance(message.channel, discord.Thread)
            and message.channel.owner != None
        ):
            if (
                message.channel.owner.bot
                and message.channel.owner.name == "Timing71Bot"
            ):
                if not message.author.bot:
                    logging.info(
                        "Deleting message from {author} in thread: {msg}".format(
                            author=message.author, msg=message.content
                        )
                    )
                    await message.delete()

        await super().on_message(message)

    async def on_disconnect(self):
        print("Discord client disconnecting")
