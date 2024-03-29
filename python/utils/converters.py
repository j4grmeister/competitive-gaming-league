from discord.ext import commands
import discord
from python.utils import database
from python.utils import cache
from concurrent.futures import ThreadPoolExecutor
import asyncio
from python.utils import selectors

class CGL_User(commands.UserConverter):
    async def convert(self, ctx, argument):
        #convert this to a Discord user and check that they are registered
        user = None
        discordid = None
        try:
            user = await super().convert(ctx, argument)
            discordid = user.id
            database.execute(f"""
                SELECT elo
                FROM server_players
                WHERE discord_id='{discordid}'
            ;""")
        except:
            database.execute(f"""
                SELECT discord_id
                FROM players
                WHERE lower(username)='{argument.lower()}'
            ;""")
            discordid, = database.fetchone()
            database.execute(f"""
                SELECT elo
                FROM server_players
                WHERE
                    server_id='{ctx.guild.id}' AND
                    discord_id='{discordid}'
            ;""")
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
            return ctx.bot.get_user(int(discordid))
        return user

class CGL_Team(commands.RoleConverter):
    async def convert(self, ctx, argument):
        #convert this into a team id, or None if it doesn't exist
        team = None
        try:
            role = await super().convert(ctx, argument)
            if role != None:
                database.execute(f"""
                    SELECT team_id
                    FROM server_teams
                    WHERE
                        server_id='{ctx.guild.id}' AND
                        role_id='{role}'
                ;""")
                team, = database.fetchone()
                if team == None:
                    await ctx.send("That team doesn't exist")
                return team
        except:
            pass
        database.execute(f"""
            SELECT
                team_id,
                team_name,
                game
            FROM teams
            WHERE lower(team_name)='{argument.lower()}'
        ;""")
        allteams = database.fetchall()
        if allteams == None:
            await ctx.send("That team doesn't exist")
            return None
        team = await selectors.select_team(ctx, teams=allteams)
        return team
