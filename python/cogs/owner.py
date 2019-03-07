import discord
from discord.ext import commands
from python import utils

class Owner:
    def __init__(self, bot):
        self.bot = bot

    async def menu_select(self, ctx, embed, options):
        funcs = []
        count = 0
        for o in options:
            embed.add_field(name=f'{utils.emoji_list[count]} {o[0]}', value=o[2])
            funcs.append(o[1])
            count += 1
        f = await utils.selectors.select_object(ctx, objects=funcs, embed=embed)
        if f != None:
            await f(ctx)

    @commands.command(pass_context=True)
    async def settings(self, ctx):
        await self.settings_home(ctx)

    async def settings_home(self, ctx):
        e = discord.Embed(title='Server Settings', description=ctx.author.mention, colour=discord.Colour.blue())
        e.set_footer(text='Home')
        options = [
            ('General Settings', self.general_settings, self.general_settings.__doc__),
            ('Team Settings', self.team_settings, self.team_settings.__doc__),
            ('Ranking Settings', self.ranking_settings, self.ranking_settings.__doc__)
        ]
        await self.menu_select(ctx, e, options)

    async def general_settings(self, ctx):
        """View and change general settings for this server."""
        e = discord.Embed(title='Server Settings', description=ctx.author.mention, colour=discord.Colour.blue())
        e.set_footer(text='Team Settings')
        utils.database.execute(f"""
            SELECT
                force_usernames
            FROM servers
            WHERE server_id='{ctx.guild.id}'
        ;""")
        force_usernames, = utils.database.fetchone()
        async def f_force_usernames(ctx):
            utils.database.execute(f"""
                UPDATE servers
                SET force_usernames={not force_usernames}
                WHERE server_id='{ctx.guild.id}'
            ;""")
            utils.database.commit()
            if not force_usernames:
                #start forcing usernames
                #change the server settings to not allow nickname changes
                #change the @everyone permissions
                everyone_role = ctx.guild.roles[0]
                perms = everyone_role.permissions
                perms.update(change_nickname=False)
                await everyone_role.edit(permissions=perms)
                #get the discord id of all players who are in this server
                utils.database.execute(f"""
                    SELECT
                        server_players.discord_id,
                        players.username
                    FROM server_players
                     INNER JOIN players
                     ON server_players.discord_id=players.discord_id
                    WHERE
                        server_players.server_id='{ctx.guild.id}' AND
                        server_players.is_member=true
                ;""")
                allmembers = utils.database.fetchall()
                for pid, username in allmembers:
                    member = ctx.guild.get_member(int(pid))
                    await member.edit(nick=username)
            await self.general_settings(ctx)
        options = [
            ('Force Usernames', f_force_usernames, ('Enabled' if force_usernames else 'Disabled')),
            ('Back', self.settings_home, 'Return to the previous page')
        ]
        await self.menu_select(ctx, e, options)
    async def team_settings(self, ctx):
        """View and change settings for teams in this server."""
        e = discord.Embed(title='Server Settings', description=ctx.author.mention, colour=discord.Colour.blue())
        e.set_footer(text='Team Settings')
        utils.database.execute(f"""
            SELECT
                team_roles_enabled,
                hoist_roles,
                mention_roles
            FROM servers
            WHERE server_id='{ctx.guild.id}'
        ;""")
        team_roles, hoist, mention = utils.database.fetchone()
        async def f_team_roles(ctx):
            pass
        async def f_hoist(ctx):
            pass
        async def f_mention(ctx):
            pass
        options = [
            ('Team Roles', f_team_roles, ('Enabled' if team_roles else 'Disabled')),
            ('Display Team Roles Separately', f_hoist, ('Enabled' if hoist else 'Disabled')),
            ('Team Roles are Mentionable', f_mention, ('Enabled' if mention else 'Disabled')),
            ('Back', self.settings_home, 'Return to the previous page')
        ]
        await self.menu_select(ctx, e, options)

    async def ranking_settings(self, ctx):
        """View and change settings for player and team ranking."""
        e = discord.Embed(title='Server Settings', description=ctx.author.mention, colour=discord.Colour.blue())
        e.set_footer(text='Ranking Settings')
        utils.database.execute(f"""
            SELECT
                default_elo,
                elo_k_factor
            FROM servers
            WHERE server_id='{ctx.guild.id}'
        ;""")
        default_elo, k_factor = utils.database.fetchone()
        async def f_default_elo(ctx):
            pass
        async def f_k_factor(ctx):
            pass
        options = [
            ('Default Elo', f_default_elo, f'{default_elo}'),
            ('K-Factor', f_k_factor, f'{k_factor}'),
            ('Back', self.settings_home, 'Return to the previous page')
        ]
        await self.menu_select(ctx, e, options)

    @commands.command(pass_context=True)
    #@utils.checks.server_owner()
    async def setting(self, ctx, key, *, value):
        utils.database.execute(f"UPDATE servers SET {key}={value} WHERE server_id='{ctx.guild.id}';")
        utils.database.commit()
        await ctx.send("Setting has been updated.")

    @commands.command(pass_context=True)
    async def reset(self, ctx):
        utils.database.execute("DELETE FROM players;")
        utils.database.execute("DELETE FROM teams;")
        utils.database.execute("DELETE FROM server_players;")
        utils.database.execute("DELETE FROM server_teams;")
        utils.database.commit()
        await ctx.send("Database reset")

def setup(bot):
    bot.add_cog(Owner(bot))
