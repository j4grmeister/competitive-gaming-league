import discord
from discord.ext import commands
from python import utils
import json

class Teams:
    def __init__(self, bot):
        self.bot = bot

    @commands.group(pass_context=True)
    @utils.checks.server_subscription()
    @utils.checks.is_registered()
    async def team(self, ctx):
        """Utilities for creating, joining, and managing teams."""
        await ctx.send("See **!help team** for a list of subcommands.")

    @team.command(pass_context=True)
    @utils.checks.server_subscription()
    @utils.checks.is_registered()
    async def create(self, ctx, *, team_name):
        """Create a new team.
        Creates a new team with this server's default game.
        You cannot be on more than one team per game."""
        if team_name == "":
            await ctx.send("Please provide a team name.")
            return
        #get the list of games for this server
        guild_games = json.loads(utils.database.server_setting(ctx.guild.id, 'games'))
        #if there is only 1 game for this server
        #continue creating the team
        if len(guild_games) == 1:
            #check that the player isnt already on a team for this server's game
            utils.database.execute(f"SELECT teams -> '{guild_games[0]}' FROM player_table WHERE discord_id={ctx.author.id};")
            player_team = utils.database.fetchone()[0]
            if player_team != None:
                await ctx.send(f"You are already on a {guild_games[0]} team.\nYou cannot be on more than one team per game.")
                return
            #generate an id for the team
            teamid = utils.generate_id()
            #escape the team name to prevent SQL injection
            eteam_name = utils.security.escape_sql(team_name)
            #get all the servers that the player is in that have this game as their primary game
            #create team roles as well
            team_elo = {}
            utils.database.execute(f"SELECT server_id, team_roles_enabled, default_role, hoist_roles, mention_roles FROM server_table WHERE '{guild_games[0]}'=ANY(games);")
            allservers = utils.database.fetchall()
            for sid, team_roles_enabled, default_role, hoist_roles, mention_roles in allservers:
                guild = self.bot.get_guild(sid)
                member = guild.get_member(ctx.author.id)
                if member != None:
                    utils.database.execute(f"SELECT elo -> {guild.id} FROM player_table WHERE discord_id={ctx.author.id};")
                    team_elo[sid] = utils.database.fetchone()[0]
                    troleid = 'NULL'
                    if team_roles_enabled:
                        drole = guild.get_role(default_role)
                        await member.remove_roles(drole)
                        trole = await guild.create_role(name=team_name, permissions=drole.permissions, colour=discord.Colour.orange(), hoist=hoist_roles, mentionable=mention_roles)
                        await member.add_roles(trole)
                        troleid = trole.id
                    utils.database.execute(f"UPDATE server_table SET teams=teams || '{{{teamid}: {troleid}}}' WHERE server_id={sid};")
            #create the team's database entry
            utils.database.execute(f"INSERT INTO team_table (team_id, game, team_name, team_elo, primaries) VALUES ({teamid}, '{guild_games[0]}', '{eteam_name}', '{team_elo}', '{{{ctx.author.id}}}');")
            #add the user to the team
            utils.database.execute(f"UPDATE player_table SET teams=teams || '{{'{guild_games[0]}': teamid}}' WHERE discord_id={ctx.author.id};")
            #commit changes
            utils.database.commit()
            await ctx.send("Your team has been created.")
        else: #send to a reaction to ask for the game for the team
            e = discord.Embed(title="Create Team", description=ctx.author.mention, colour=discord.Colour.blue())
            gamelist = ""
            count = 0
            for game in guild_games:
                if len(gamelist) > 0:
                    gamelist += '\n'
                gamelist += f"{utils.emoji_list[index]} {game}"
                count += 1
            e.add_field(name="Choose a game for your team", value=gamelist)
            msg = await ctx.send(embed=e)
            for x in range(count):
                await msg.add_reaction(utils.emoji_list[x])
            utils.cache.add('create_team_message', msg.id, {'team_name': team_name, 'user': ctx.author.id, 'guild_games': guild_games})

    @team.command(pass_context=True)
    @utils.checks.server_subscription()
    @utils.checks.is_team_owner()
    async def changename(self, ctx, *, team_name):
        if team_name == "":
            await ctx.send("Please provide a team name.")
            return
        owned_teams = utils.teams.get_owned_teams(ctx.guild.id, ctx.author.id)
        if len(owned_teams) == 1:
            utils.database.execute("SELECT server_id, teams FROM server_table WHERE team_roles_enabled=TRUE;")
            allservers = utils.database.fetchall()
            for sid, teams_json in allservers:
                teams = json.loads(teams_json)
                if owned_teams[0] in teams:
                    guild = self.bot.get_guild(sid)
                    role = guild.get_role(teams[owned_teams[0]])
                    await role.edit(name=team_name)
            eteam_name = utils.security.escape_sql(team_name)
            utils.database.execute(f"UPDATE team_table SET team_name='{eteam_name}' WHERE team_id={owned_teams[0]};")
            utils.database.commit()
            await ctx.send("Your team name has been changed.")
        else:
            e = discord.Embed(title="Change team name", description=ctx.author.mention, colour=discord.Colour.blue())
            teamlist = ""
            count = 0
            for team in owned_teams:
                if len(teamlist) > 0:
                    teamlist += '\n'
                utils.database.execute(f"SELECT team_name, game FROM team_table WHERE team_id={team};")
                tname, game = utils.database.fetchone()
                teamlist += f"{utils.emoji_list[count]} {tname} ({game})"
                count += 1
            e.add_field(name="Choose a team to change", value=teamlist)
            msg = await ctx.send(embed=e)
            for x in range(count):
                await msg.add_reaction(utils.emoji_list[x])
            utils.cache.add('change_team_name_message', msg.id, {'team_name': team_name, 'user': ctx.author.id, 'owned_teams': owned_teams})

    @team.command(pass_context=True)
    @utils.checks.server_subscription()
    @utils.checks.is_team_owner()
    async def invite(self, ctx, user: discord.User):
        if user == None:
            await ctx.send("That player could not be identified.")
            return
        #check that the target user has registered
        utils.database.execute(f"SELECT username FROM player_table WHERE discord_id={user.id};")
        username, = utils.database.fetchone()
        if username == None:
            await ctx.send("That player is not registered.\nThey can register with **!register <username>**")
            return
        #get the author's owned teams
        owned_teams = utils.teams.get_owned_teams(ctx.guild.id, ctx.author.id)
        if len(owned_teams) == 1:
            #check that the player is not already on a team for this game
            game = utils.teams.team_game(owned_teams[0])
            utils.database.execute(f"SELECT teams -> '{game}' FROM player_table WHERE discord_id={user.id};")
            player_team = utils.database.fetchone()[0]
            if player_team != None:
                await ctx.send(f"That player is already on a {game} team.\nYou cannot be on more than one team per game.")
                return
            team_name = utils.teams.team_name(owned_teams[0])
            e = discord.Embed(title="Team invite", description=f"From {ctx.author.mention}", colour=discord.Colour.blue())
            e.add_field(name=f"You have been invited to {team_name};", value=f"React with {utils.emoji_confirm} to accept or {utils.emoji_decline} to decline.")
            msg = await user.send(embed=e)
            await msg.add_reaction(utils.emoji_confirm)
            await msg.add_reaction(utils.emoji_decline)
            utils.cache.add('team_invite_message', msg.id, owned_teams[0])
            await ctx.send(f"{username} has been invited to {team_name}.")
        else:
            e = discord.Embed(title="Invite player", description=ctx.author.mention, colour=discord.Colour.blue())
            teamlist = ""
            count = 0
            for team in owned_teams:
                if len(teamlist) > 0:
                    teamlist += '\n'
                utils.database.execute(f"SELECT team_name, game FROM team_table WHERE team_id={team};")
                tname, game = utils.database.fetchone()
                teamlist += f"{utils.emoji_list[count]} {tname} ({game})"
                count += 1
            e.add_field(name="Choose a team to send an invite to", value=teamlist)
            msg = await ctx.send(embed=e)
            for x in range(count):
                await msg.add_reaction(utils.emoji_list[x])
            utils.cache.add('invite_to_team_message', msg.id, {'team_name': team_name, 'author': ctx.author, 'user': user, 'owned_teams': owned_teams})

def setup(bot):
    bot.add_cog(Teams(bot))
