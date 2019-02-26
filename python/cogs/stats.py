import discord
from discord.ext import commands
from python import utils

class Stats:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def teamlist(self, ctx, page=1):
        e = discord.Embed(title='Team List', colour=discord.Colour.blue())
        utils.database.execute(f"""SELECT teams.team_name,
                server_teams.role_id,
                server_teams.team_elo
            FROM server_teams
            INNER JOIN teams ON server_teams.team_id=teams.team_id
            WHERE server_teams.server_id='{ctx.guild.id}'
                AND (array_length(server_teams.primary_players, 0)>0 OR array_length(server_teams.substitute_players, 0)>0)
            ORDER BY server_teams.team_elo DESC
            LIMIT 10 OFFSET {(page-1)*10};""")
        tlist = utils.database.fetchall()
        team_str = ""
        index = (page-1)*10+1
        for team_name, role_id, team_elo in tlist:
            if len(team_str) > 0:
                team_str += '\n'
            team = team_name
            if role_id != None:
                team = ctx.guild.get_role(int(role_id)).mention
            team_str += f"**{index})** {team} - {team_elo}"
        e.add_field(name='Team - Elo', value=team_str)
        e.set_footer(text=f"Page 1")
        await ctx.send(embed=e)

    @commands.command(pass_context=True)
    async def playerinfo(self, ctx, player: utils.converters.CGL_User):
        if player == None:
            return
        #get player data
        utils.database.execute(f"SELECT username, teams, server_roles -> '{ctx.guild.id}', awards -> '{ctx.guild.id}' FROM players WHERE discord_id='{player.id}';")
        username, teams, roles, awards = utils.database.fetchone()
        utils.database.execute(f"SELECT game, elo FROM server_players WHERE server_id='{ctx.guild.id}' AND discord_id='{player.id}';")
        allelo = utils.database.fetchall()
        e = discord.Embed(title=username, description=player.mention, colour=discord.Colour.blue())
        e.set_image(url=player.avatar_url)
        #elo and teams
        elo_str = ""
        teams_str = ""
        for game, elo in allelo:
            elo_str += f"**{game}:** {elo}\n"
            if game in teams:
                utils.database.execute(f"SELECT team_name FROM teams WHERE team_id='{teams[game]}';")
                teamname, = utils.database.fetchone()
                teams_str += f"**{game}:** {teamname}\n"
        elo_str = elo_str[:-1]
        e.add_field(name='Elo', value=elo_str)
        if len(teams_str) > 0:
            teams_str = teams_str[:-1]
            e.add_field(name='Team', value=teams_str)
        #server roles
        roles_str = ""
        for r in roles:
            roles_str += f"{ctx.guild.get_role(int(r)).name}\n"
        if len(roles_str) > 0:
            roles_str = roles_str[:-1]
            e.add_field(name='Roles', value=roles_str)
        #awards
        awards_str = ""
        for a in awards:
            awards_str += f"{a}\n"
        if len(awards_str) > 0:
            awards_str = awards_str[:-1]
            e.add_field(name='Awards', value=awards_str)
        await ctx.send(embed=e)

    @commands.command(pass_context=True)
    async def teaminfo(self, ctx, *, team: utils.converters.CGL_Team):
        if teamid == None:
            return
        database.execute(f"SELECT team_name, primary_players, substitute_players FROM teams WHERE team_id='{teamid}';")
        teamname, primary_players, substitute_players = database.fetchone()
        database.execute(f"SELECT team_elo, role_id FROM server_teams WHERE server_id='{ctx.guild.id}' AND team_id='{teamid}';")
        teamelo, roleid = database.fetchone()
        desc = ""
        if roleid != None:
            desc = ctx.guild.get_role(int(roleid)).mention
        e = discord.Embed(title=teamname, description=desc, colour=discord.Colour.blue())
        e.add_field(name='Team Elo', value=teamelo)

        primary_str = ""
        for player in primary_players:
            member = ctx.guild.get_member(int(player))
            if member != None:
                if len(primary_str) > 0:
                    primary_str += '\n'
                primary_str += member.mention
        if len(primary_str) > 0:
            e.add_field(name='Primary', value=primary_str)

        sub_str = ""
        for player in substitute_players:
            member = ctx.guild.get_member(int(player))
            if member != None:
                if len(sub_str) > 0:
                    sub_str += '\n'
                sub_str += member.mention
        if len(sub_str) > 0:
            e.add_field(name='Subs', value=sub_str)
        await ctx.send(embed=e)

def setup(bot):
    bot.add_cog(Stats(bot))
