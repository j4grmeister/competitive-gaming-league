from discord.ext import commands
import discord
from python.utils import database

class CGL_User(commands.UserConverter):
    async def convert(self, ctx, argument):
        #convert this to a Discord user and check that they are registered
        user = None
        try:
            user = await super().convert(ctx, argument)
        if user == None:
            database.execute(f"SELECT elo, discord_id FROM player_table WHERE lower(username)='{argument.lower()}';")
        else:
            database.execute(f"SELECT elo, discord_id FROM player_table WHERE discord_id={user.id};")
        elo, discordid = database.fetchone()
        if elo == None:
            if user == None:
                await ctx.send("That user doesn't exist.")
            else:
                await ctx.send("That user is not registered.\nSee **!help register** for more details.")
            return None
        #check that the user is a member of this server
        if f"{ctx.guild.id}" not in elo:
            await ctx.send("That user is not a member of this server.")
            return None
        if user == None:
            return ctx.bot.get_user(discordid)
        return user
