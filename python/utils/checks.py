from discord.ext import commands
import discord
from python.utils import database

def server_subscription():
    async def predicate(ctx):
        #TODO: add server subscription support
        return True
    return commands.check(predicate)

def is_registered():
    async def predicate(ctx):
        database.execute(f"""
            SELECT username
            FROM players
            WHERE discord_id='{ctx.author.id}'
        ;""")
        r = (database.fetchone() != None)
        if not ctx.message.content.startswith('!help') and not r:
            await ctx.send("You must be registered to use that command.\nYou can register with **!register <username>**")
        return r
    return commands.check(predicate)

def not_registered():
    async def predicate(ctx):
        database.execute(f"""
            SELECT username
            FROM players
            WHERE discord_id='{ctx.author.id}'
        ;""")
        r = (database.fetchone() == None)
        if not ctx.message.content.startswith('!help') and not r:
            await ctx.send("You have already registered.\nYou can change your name with **!changename <username>**")
        return r
    return commands.check(predicate)

def is_on_team():
    async def predicate(ctx):
        database.execute(f"""
            SELECT t.team
            FROM (
                SELECT unnest(teams) AS team
                FROM players
                WHERE discord_id='{ctx.author.id}'
            ) AS t
                INNER JOIN teams
                ON t.team=teams.team_id
            WHERE
                teams.game=ANY(
                    SELECT unnest(games)
                    FROM servers
                    WHERE server_id='{ctx.guild.id}'
                )
        ;""")
        return (database.fetchall() != None)
    return commands.check(predicate)

def is_team_owner():
    async def predicate(ctx):
        database.execute(f"""
            SELECT team_id
            FROM teams
            WHERE
                owner_id='{ctx.author.id}' AND
                game=ANY(
                    SELECT
                        UNNEST(games) as games
                    FROM servers
                    WHERE server_id='{ctx.guild.id}'
        );""")
        team_id = database.fetchone()
        if team_id == None:
            return False
        return True
    return commands.check(predicate)

def server_owner():
    async def predicate(ctx):
        #TODO: actually validate this
        #database.execute(f"SELECT owner_id FROM servers WHERE server_id={ctx.guild.id};")
        #oid = database.fetchone()[0]
        #return (oid == ctx.author.id)
        return True
    return commands.check(predicate)
