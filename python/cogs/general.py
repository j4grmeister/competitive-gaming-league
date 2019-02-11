import discord
from discord.ext import commands
from python import utils
import json

class General:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @utils.checks.server_subscription()
    @utils.checks.not_registered()
    async def register(self, ctx, *, username):
        """Register as a player in the CGL database.
        Players will not have access to certain commands until they register.
        If you have registered with the CGL in the past, you do not need to do so again."""
        serverid = ctx.message.guild.id
        #check if there is no username
        if username == "":
            await ctx.send("Please provide a username.")
            return
        #check that there is no whitespace in the username
        if ' ' in username:
            await ctx.send("Spaces are not allowed in usernames.")
            return
        #escape single quotes to prevent SQL injection
        eusername = utils.security.escape_sql(username)
        #check that the username is available
        utils.database.execute(f"SELECT discord_id FROM player_table WHERE lower(username)='{eusername.lower()}';")
        if utils.database.fetchone() != None:
            await ctx.send("That username is already taken. Please try again with a different one.")
            return
        #enter the user in the database
        utils.database.execute(f"INSERT INTO player_table (discord_id, username) values ({ctx.author.id}, '{eusername}');")
        #apply server settings in all servers
        default_elo = {}
        server_roles = {}
        utils.database.execute("SELECT server_id, force_usernames, team_roles_enabled FROM server_table;")
        serverlist = utils.database.fetchall()
        for sid, force, roles in serverlist:
            guild = self.bot.get_guild(sid)
            member = guild.get_member(ctx.author.id)
            if member != None:
                default_elo[sid] = utils.database.server_setting(sid, 'default_elo')
                if force:
                    await member.edit(nick=username)
                if roles:
                    await member.add_roles(guild.get_role(utils.database.server_setting(sid, 'default_role')))
        utils.database.execute(f"UPDATE player_table SET elo=elo::jsonb || '{json.dumps(default_elo)}'::jsonb WHERE discord_id={ctx.author.id};")
        utils.database.execute(f"UPDATE player_table SET server_roles=server_roles::jsonb || '{json.dumps(server_roles)}'::jsonb WHERE discord_id={ctx.author.id};")
        #commit changes
        utils.database.commit()
        #notify the user that they have successfully registered
        await ctx.send("You have successfully registered.")

    @commands.command(pass_context=True)
    @utils.checks.server_subscription()
    @utils.checks.is_registered()
    async def changename(self, ctx, *, username):
        """Change your username."""
        serverid = ctx.message.id
        #check if there is no username
        if username == "":
            await ctx.send("Please provide a username.")
            return
        #check that there is no whitespace in the username
        if ' ' in username:
            await ctx.send("Spaces are not allowed in usernames.")
            return
        #escape single quotes to prevent SQL injection
        eusername = utils.security.escape_sql(username)
        #check that the username is available
        utils.database.execute(f"SELECT discord_id FROM player_table WHERE lower(username)='{eusername.lower()}';")
        if utils.database.fetchone() != None:
            await ctx.send("That username is already taken. Please try again with a different one.")
            return
        #update the database
        utils.database.execute(f"UPDATE player_table SET username='{eusername}' WHERE discord_id={ctx.author.id};")
        #update nickname in all servers
        utils.database.execute("SELECT server_id FROM server_table WHERE force_usernames=TRUE;")
        serverlist = utils.database.fetchall()
        for sid, in serverlist:
            member = self.bot.get_guild(sid).get_member(ctx.author.id)
            if member != None:
                await member.edit(nick=username)
        #commit changes
        utils.database.commit()
        #notify the user that they have changed their name
        await ctx.send("Your username has been changed.")

    @commands.command(pass_context=True)
    @utils.checks.server_subscription()
    @utils.checks.is_registered()
    async def setregion(self, ctx):
        """Choose your region."""
        e = discord.Embed(title="Set Region", description=ctx.author.mention, colour=discord.Colour.blue())
        e.add_field(name="Choose your region", value="React with your region below")
        msg = await ctx.send(embed=e)
        await msg.add_reaction('🇺🇸')
        await msg.add_reaction('🇪🇺')
        utils.cache.add('set_region_message', msg.id, ctx.author.id)

    @commands.command(pass_context=True)
    @utils.checks.server_subscription()
    @utils.checks.is_registered()
    async def getroles(self, ctx):
        """Request server roles."""
        e = discord.Embed(title="Get Roles", description=ctx.author.mention, colour=discord.Colour.blue())
        roles = utils.database.server_setting(ctx.guild.id, 'requestable_roles')
        field_value = ""
        valid = True
        role_count = 0
        if len(roles) > 0:
            for rolename in roles:
                if len(field_value) > 0:
                    field_value += '\n'
                field_value += f"{utils.emoji_list[count]} {rolename}"
                role_count += 1
        else:
            field_value = "There are no requestable roles for this server."
            valid = False
        e.add_field(name="Choose your roles", value=field_value)
        msg = await ctx.send(embed=e)
        if not valid:
            return
        for x in range(role_count):
            await msg.add_reaction(utils.emoji_list[x])
        await msg.add_reaction(utils.emoji_confirm)
        utils.cache.add('get_roles_message', msg.id, ctx.author.id)

def setup(bot):
    bot.add_cog(General(bot))
