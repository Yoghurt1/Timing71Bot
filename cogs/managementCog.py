from discord.ext import commands
from discord_config import Settings


class ManagementCog(commands.Cog):
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
    @commands.is_owner()
    async def setadminrole(self, ctx, roleName):
        self._config.set("adminRole", roleName)
        self._config.save()
        await ctx.send("Set admin role to " + roleName)

    @commands.command()
    @commands.is_owner()
    async def setmodrole(self, ctx, roleName):
        self._config.set("modRole", roleName)
        self._config.save()
        await ctx.send("Set mod role to " + roleName)

    @commands.command()
    @commands.has_any_role(_config.adminRole, _config.modRole)
    async def channel(self, ctx):
        await ctx.send(
            "https://media.discordapp.net/attachments/293550896950935552/804399368638824479/Wrong_channel.jpg?width=744&height=380"
        )


async def setup(bot):
    await bot.add_cog(ManagementCog(bot))
