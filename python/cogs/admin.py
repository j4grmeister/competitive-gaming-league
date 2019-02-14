import discord
from discord.ext import commands
from python import utils
import json

class Admin():
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    async def award(self, ctx):
        """Commands for managing player/team awards."""
        await ctx.send("See **!help award** for proper usage.")

    @award.command(pass_context=True)
    async def player(self, ctx, player: utils.converters.CGL_User, *, award):
        """Award a player."""
        if player == None:
            return
        if award == "":
            await ctx.send("No award was specified.")
            return
        utils.database.execute(f"UPDATE player_table SET awards=jsonb_set(awards::jsonb, array['{ctx.guild.id}'], (awards->'{ctx.guild.id}')::jsonb || '[\"{award}\"]') WHERE discord_id={player.id};")
        utils.database.commit()
        await ctx.send("That player has been awarded.")

def setup(bot):
    bot.add_cog(Admin(bot))
