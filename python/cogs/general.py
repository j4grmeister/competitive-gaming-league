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
        utils.database.execute(f"""
            SELECT
                discord_id
            FROM players
            WHERE lower(username)='{eusername.lower()}'
        ;""")
        if utils.database.fetchone() != None:
            await ctx.send("That username is already taken. Please try again with a different one.")
            return
        #enter the user in the database
        utils.database.execute(f"""
            INSERT INTO players (
                discord_id,
                username
            )
            VALUES (
                '{ctx.author.id}',
                '{eusername}'
            );""")
        #apply server settings in all servers
        utils.database.execute("""
            SELECT
                server_id,
                force_usernames,
                team_roles_enabled,
                games
            FROM servers;
        """)
        serverlist = utils.database.fetchall()
        for sid, force, roles, games in serverlist:
            guild = self.bot.get_guild(int(sid))
            member = guild.get_member(ctx.author.id)
            if member != None:
                for g in games:
                    delo = utils.database.server_setting(sid, 'default_elo')
                    utils.database.execute(f"""
                        INSERT INTO server_players (
                            discord_id,
                            server_id,
                            game,
                            elo
                        )
                        VALUES (
                            '{ctx.author.id}',
                            '{sid}',
                            '{g}',
                            {delo})
                        ;""")
                if force:
                    if member.id != guild.owner.id:
                        await member.edit(nick=username)
                if roles:
                    await member.add_roles(guild.get_role(int(utils.database.server_setting(sid, 'default_role'))))
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
        utils.database.execute(f"""
            SELECT discord_id
            FROM players
            WHERE lower(username)='{eusername.lower()}'
        ;""")
        if utils.database.fetchone() != None:
            await ctx.send("That username is already taken. Please try again with a different one.")
            return
        #update the database
        utils.database.execute(f"""
            UPDATE players
            SET username='{eusername}'
            WHERE discord_id='{ctx.author.id}'
        ;""")
        #update nickname in all servers
        utils.database.execute("""
            SELECT server_id
            FROM servers
            WHERE force_usernames=TRUE
        ;""")
        serverlist = utils.database.fetchall()
        for sid, in serverlist:
            member = self.bot.get_guild(int(sid)).get_member(ctx.author.id)
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
        region = await utils.selectors.select_string(ctx, options=['🇺🇸', '🇪🇺'], title='Set Region', inst='React with your region below')
        if region == None:
            return
        member_region == None
        if region == '🇺🇸':
            member_region = "NA"
        elif region == '🇪🇺':
            member_region = "EU"
        utils.database.execute(f"""
            UPDATE players
            SET region='{member_region}'
            WHERE discord_id='{ctx.author.id}'
        ;""")
        #grant region roles in all servers
        utils.database.execute(f"""
            SELECT
                server_id,
                region_roles -> '{member_region}'
            FROM servers
            WHERE region_roles_enabled=TRUE
        ;""")
        serverlist = utils.database.fetchall()
        for sid, role in serverlist:
            guild = bot.get_guild(int(sid))
            member = guild.get_member(ctx.author.id)
            await member.add_roles(guild.get_role(int(role)))
        utils.database.commit()
        await ctx.send("Your region has been updated.")

def setup(bot):
    bot.add_cog(General(bot))
