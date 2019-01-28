from discord.ext import commands
import discord
import python.utils.database

def server_subscription():
    async def predicate(ctx):
        #TODO: add server subscription support
        return True
    return commands.check(predicate)

def is_registered():
    async def predicate(ctx):
        database.execute(f"SELECT username FROM playertable WHERE discordid={ctx.author.id};")
        r = (database.fetchone() != None)
        if not r:
            await ctx.send("You must be registered to use that command.\nYou can register with **!register <username>**")
        return r
    return commands.check(predicate)

def not_registered():
    async def predicate(ctx):
        database.execute(f"SELECT username FROM playertable WHERE discordid={ctx.author.id};")
        r = (database.fetchone() == None)
        if not r:
            await ctx.send("You have already registered.\nYou can change your name with **!changename <username>**")
        return r
    return commands.check(predicate)

def is_team_owner():
    async def predicate(ctx):
        database.execute(f"SELECT team_id FROM team_table WHERE owner_id={ctx.author.id} AND game=ANY(SELECT games FROM server_table WHERE server_id={ctx.guild.id});")
        team_id = database.fetchone()
        if team_id == None:
            return False
        return True

    return commands.check(predicate)
