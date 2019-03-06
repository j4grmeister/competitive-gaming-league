import discord
from discord.ext import commands
from python import utils
import json

class Teams:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    @utils.checks.server_subscription()
    @utils.checks.is_registered()
    async def createteam(self, ctx, *, team_name):
        """Create a new team.
        Creates a new team with this server's default game.
        You cannot be on more than one team per game."""
        if team_name == "":
            await ctx.send("Please provide a team name.")
            return
        #get the list of games for this server
        guild_games = utils.database.server_setting(ctx.guild.id, 'games')
        #have the user select a game
        game = await utils.selectors.select_string(ctx, options=guild_games, title='Select Game', inst='Choose a game for your team')
        if game == None:
            return
        #check that the player isnt already on a team for this server's game
        utils.database.execute(f"""
            SELECT team_id
            FROM teams
            WHERE
                team_id=ANY(
                    SELECT unnest(teams)
                    FROM players
                    WHERE discord_id='{ctx.author.id}'
                ) AND
                game='{game}'
        ;""")
        player_team = utils.database.fetchone()
        if player_team != None:
            await ctx.send(f"You are already on a {game} team.\nYou cannot be on more than one team per game.")
            return
        #generate an id for the team
        teamid = utils.generate_id()
        #escape the team name to prevent SQL injection
        eteam_name = utils.security.escape_sql(team_name)
        #get all the servers that the player is in that have this game as their primary game
        #create team roles as well
        utils.database.execute(f"""
            SELECT
                server_id,
                team_roles_enabled,
                hoist_roles,
                mention_roles
            FROM servers
            WHERE '{game}'=ANY(games)
        ;""")
        allservers = utils.database.fetchall()
        for sid, team_roles_enabled, hoist_roles, mention_roles in allservers:
            guild = self.bot.get_guild(int(sid))
            member = guild.get_member(ctx.author.id)
            if member != None:
                utils.database.execute(f"""
                    SELECT elo
                    FROM server_players
                    WHERE
                        game='{game}' AND
                        server_id='{ctx.guild.id}' AND
                        discord_id='{ctx.author.id}'
                ;""")
                team_elo, = utils.database.fetchone()
                troleid = '-1' #-1 means no role
                if team_roles_enabled:
                    trole = await guild.create_role(name=team_name, colour=discord.Colour.orange(), hoist=hoist_roles, mentionable=mention_roles)
                    await member.add_roles(trole)
                    troleid = str(trole.id)
                utils.database.execute(f"""
                    INSERT INTO server_teams (
                        server_id,
                        team_id,
                        team_elo,
                        role_id,
                        primary_players
                    ) VALUES (
                        '{guild.id}',
                        '{teamid}',
                        {team_elo},
                        '{troleid}',
                        '{{ \"{ctx.author.id}\" }}'
                );""")
        #create the team's database entry
        utils.database.execute(f"""
            INSERT INTO teams (
                owner_id,
                team_id,
                game,
                team_name,
                primary_players
            ) VALUES (
                '{ctx.author.id}',
                '{teamid}',
                '{game}',
                '{eteam_name}',
                '{{ \"{ctx.author.id}\" }}'
        );""")
        #add the user to the team
        utils.database.execute(f"""
            UPDATE players
            SET
                teams=array_append(teams, '{teamid}')
            WHERE discord_id='{ctx.author.id}'
        ;""")
        #commit changes
        utils.database.commit()
        await ctx.send("Your team has been created.")

    @commands.command(pass_context=True)
    @utils.checks.server_subscription()
    @utils.checks.is_team_owner()
    async def changeteamname(self, ctx, *, team_name):
        if team_name == "":
            await ctx.send("Please provide a team name.")
            return
        #get the author's owned teams
        utils.database.execute(f"""
            SELECT
                team_id,
                team_name,
                game
            FROM teams
            WHERE
                owner_id='{ctx.author.id}' AND
                game=ANY(
                    SELECT games
                    FROM servers
                    WHERE server_id='{ctx.guild.id}'
        );""")
        owned_teams = utils.database.fetchall()
        team = await utils.selectors.select_team(ctx, teams=owned_teams, title='Select Team', inst='Select a team to change its name')
        if team == None:
            return
        utils.database.execute(f"""
            SELECT
                server_teams.server_id,
                server_teams.role_id
            FROM server_teams
            INNER JOIN servers
                ON server_teams.server_id=servers.server_id
            WHERE
                server_teams.team_id='{team}' AND
                servers.team_roles_enabled=TRUE
        ;""")
        allservers = utils.database.fetchall()
        for sid, role_id in allservers:
            guild = self.bot.get_guild(int(sid))
            role = guild.get_role(int(role_id))
            await role.edit(name=team_name)
        eteam_name = utils.security.escape_sql(team_name)
        utils.database.execute(f"""
            UPDATE teams
            SET team_name='{eteam_name}'
            WHERE team_id='{team}'
        ;""")
        utils.database.commit()
        await ctx.send("Your team name has been changed.")

    @commands.command(pass_context=True)
    @utils.checks.server_subscription()
    @utils.checks.is_team_owner()
    async def invite(self, ctx, user: utils.converters.CGL_User):
        if user == None:
            await ctx.send("That player could not be identified.")
            return
        #check that the target user has registered
        utils.database.execute(f"""
            SELECT username
            FROM players
            WHERE discord_id='{user.id}'
        ;""")
        username, = utils.database.fetchone()
        if username == None:
            await ctx.send("That player is not registered.\nThey can register with **!register <username>**")
            return
        #get the author's owned teams
        utils.database.execute(f"""
            SELECT
                team_id,
                team_name,
                game
            FROM teams
            WHERE
                owner_id='{ctx.author.id}' AND
                game=ANY(
                    SELECT unnest(games)
                    FROM servers
                    WHERE server_id='{ctx.guild.id}'
        );""")
        owned_teams = utils.database.fetchall()
        #have the user select a team they own
        team = await utils.selectors.select_team(ctx, teams=owned_teams, title='Select Team', inst='Select a team to send an invite for')
        if team == None:
            return
        #check that the player is not already on a team for this game
        game = utils.teams.team_game(team)
        utils.database.execute(f"""
            SELECT teams.team_id
            FROM teams
                INNER JOIN players
                ON teams.team_id=ANY(players.teams)
            WHERE
                players.discord_id='{user.id}' AND
                teams.game='{game}'
        ;""")
        player_team, = utils.database.fetchone()
        if player_team != None:
            await ctx.send(f"That player is already on a {game} team.\nYou cannot be on more than one team per game.")
            return
        #invite the target user
        team_name = utils.teams.team_name(team)
        e = discord.Embed(title="Team invite", description=f"From {ctx.author.mention}", colour=discord.Colour.blue())
        e.add_field(name=f"You have been invited to {team_name};", value=f"React with {utils.emoji_confirm} to accept or {utils.emoji_decline} to decline.")
        msg = await user.send(embed=e)
        await msg.add_reaction(utils.emoji_confirm)
        await msg.add_reaction(utils.emoji_decline)
        utils.cache.add('team_invite_message', msg.id, team)
        await ctx.send(f"{username} has been invited to {team_name}.")

def setup(bot):
    bot.add_cog(Teams(bot))
