import discord
from discord.ext import commands
from python import utils

class Owner:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @utils.checks.server_owner()
    async def setting(self, ctx, key, value):
        utils.database.execute(f"UPDATE server_table SET {key}={value} WHERE server_id={ctx.guild.id};")
        utils.database.commit()
        await ctx.send("Setting has been updated.")

def setup(bot):
    bot.add_cog(Owner(bot))
