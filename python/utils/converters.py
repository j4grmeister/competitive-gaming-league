from discord.ext import commands
import discord
from python.utils import database
from python.utils import cache
from concurrent.futures import ThreadPoolExecutor
import asyncio

class CGL_User(commands.UserConverter):
    async def convert(self, ctx, argument):
        #convert this to a Discord user and check that they are registered
        user = None
        try:
            user = await super().convert(ctx, argument)
            database.execute(f"SELECT elo, discord_id FROM player_table WHERE discord_id={user.id};")
        except:
            database.execute(f"SELECT elo, discord_id FROM player_table WHERE lower(username)='{argument.lower()}';")
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

class CGL_Team(commands.RoleConverter):
    async def convert(self, ctx, argument):
        #convert this into a team id, or None if it doesn't exist
        #team = None
        #try:
        #    team = await super().convert(ctx, argument)
        #    database.execute(f"SELECT team_id FROM team_table WHERE )
        #except:
        #    database.execute(f"SELECT )
        finished = False
        def done():
            finished = True
        msg = await ctx.send("react")
        cache.add('test', msg.id, done)
        while(not finished):
            await asyncio.sleep(1)
        return 'success'
