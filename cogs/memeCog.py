from discord.ext import commands
from discord_config import Settings
from datetime import date


class MemeCog(commands.Cog):
    _config = Settings(
        defaults={
            "adminRole": "Admin",
            "modRole": "Tiddy Boiz",
            "delay": 0,
            "excludes": [],
        },
        filename="config.json",
    )

    def __init__(self, bot, config=None):
        self.bot = bot

    @commands.command()
    async def driftercount(self, ctx):
        initDate = date(2020, 10, 5)
        now = date.today()
        delta = now - initDate
        await ctx.send("{0} days".format(delta.days))


def setup(bot):
    bot.add_cog(MemeCog(bot))
