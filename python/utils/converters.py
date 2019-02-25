from discord.ext import commands
import discord
from python.utils import database
from python.utils import cache
from concurrent.futures import ThreadPoolExecutor
import asyncio
import python.utils.teams

class CGL_User(commands.UserConverter):
    async def convert(self, ctx, argument):
        #convert this to a Discord user and check that they are registered
        user = None
        discordid = None
        try:
            user = await super().convert(ctx, argument)
            discordid = user.id
            database.execute(f"SELECT elo FROM server_players WHERE discord_id='{discordid}';")
        except:
            database.execute(f"SELECT discord_id FROM players WHERE lower(username)='{argument.lower()}';")
            discordid, = database.fetchone()
            database.execute(f"SELECT elo FROM server_players WHERE server_id='{ctx.guild.id}' AND discord_id='{discordid}';")
        elo, = database.fetchone()
        if discordid == None:
            if user == None:
                await ctx.send("That user doesn't exist.")
            else:
                await ctx.send("That user is not registered.\nSee **!help register** for more details.")
            return None
        else:
            if elo == None:
                await ctx.send("That user is not a member of this server.")
                return None
        if user == None:
            return ctx.bot.get_user(discordid)
        return user

class CGL_Team(commands.RoleConverter):
    async def convert(self, ctx, argument):
        #convert this into a team id, or None if it doesn't exist
        team = None
        try:
            role = await super().convert(ctx, argument)
            if role != None:
                database.execute(f"SELECT team_id FROM (SELECT json_each(teams) FROM servers WHERE server_id='{ctx.guild.id}') AS (team_id KEY, role_id TEXT) WHERE role_id='{role}';")
                team, = database.fetchone()
                if team == None:
                    await ctx.send("That team doesn't exist")
                    return None
        except:
            pass
        database.execute(f"SELECT team_id FROM teams WHERE lower(team_name)='{argument.lower()}';")
        allteams = database.fetchall()
        if allteams == None:
            await ctx.send("That team doesn't exist")
            return None
        for i in range(len(allteams)):
            allteams[i] = allteams[i][0]
            team = teams.select_team(allteams)
            if team == None:
                return None
        return team
