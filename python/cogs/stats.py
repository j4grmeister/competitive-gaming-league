import discord
from discord.ext import commands
from python import utils

class Stats:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def playerinfo(self, ctx, player: utils.converters.CGL_User):
        if player == None:
            return
        #get player data
        utils.database.execute(f"SELECT username, teams, server_roles -> '{ctx.guild.id}', awards -> '{ctx.guild.id}' FROM players WHERE discord_id={player.id};")
        username, teams, roles, awards = utils.database.fetchone()
        utils.database.execute(f"SELECT game, elo FROM server_players WHERE server_id={ctx.guild.id} AND discord_id={player.id};")
        allelo = utils.database.fetchall()
        e = discord.Embed(title=username, description=player.mention, colour=discord.Colour.blue(), image=player.avatar_url)
        #elo and teams
        elo_str = ""
        teams_str = ""
        for game, elo in allelo:
            elo_str += f"**{game}:** {elo}\n"
            if game in teams:
                utils.database.execute(f"SELECT team_name FROM teams WHERE team_id={teams[game]}")
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
            roles_str += f"{ctx.guild.get_role(r).name}\n"
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
        await ctx.send(team)

def setup(bot):
    bot.add_cog(Stats(bot))
