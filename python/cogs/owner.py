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
            ('Ranking Settings', self.rank_settings, self.rank_settings.__doc__)
        ]
        await self.menu_select(ctx, e, options)

    async def general_settings(self, ctx):
        """View and change general settings for this server."""
        e = discord.Embed(title='Server Settings', description=ctx.author.mention, colour=discord.Colour.blue())
        e.set_footer(text='Team Settings')
        utils.database.execute(f"""
            SELECT
                force_usernames,
                games
            FROM servers
            WHERE server_id='{ctx.guild.id}'
        ;""")
        force_usernames, games = utils.database.fetchone()
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
        async def f_games(ctx):
            ge = discord.Embed(title='Server Settings', description=ctx.author.mention, colour=discord.Colour.blue())
            ge.set_footer(text='Games')
            games_str = ""
            count = 0
            for g in utils.config.games.keys():
                if len(games_str) > 0:
                    games_str += '\n'
                games_str += f"{utils.emoji_list[count]} {g} {utils.emoji_confirm if g in games else utils.emoji_decline}"
                count += 1
            ge.add_field(name='Select to toggle on/off', value=games_str)
            tog_game = await utils.selectors.select_object(ctx, objects=list(utils.config.games.keys()), embed=ge)
            #don't continue if the operation timed out
            if tog_game != None:
                #ask the user to confirm removing games
                if tog_game in games:
                    coninue_remove = await utils.selectors.confirm(ctx, title='Server Settings', warning='Remove games?', footer='Games', message=f'Are you sure you would like to remove {tog_game} from this server?\n*If you wish to migrate game data to another server, contact {self.bot.appinfo.owner.mention}.*')
                    if continue_remove:
                        utils.database.execute(f"""
                            UPDATE servers
                            SET games=array_remove(games, '{tog_game}')
                            WHERE server_id='{ctx.guild.id}'
                        ;""")
                        #TODO: remove team roles
                else:
                    utils.database.execute(f"""
                        SELECT
                            default_elo
                        FROM servers
                        WHERE server_id='{ctx.guild.id}'
                    ;""")
                    default_elo, = utils.database.fetchone()
                    utils.database.execute(f"""
                        UPDATE servers
                        SET games=array_append(games, '{g}')
                        WHERE server_id='{ctx.guild.id}'
                    ;""")
                    utils.database.execute(f"""
                        INSERT INTO server_players (
                            discord_id,
                            server_id,
                            game,
                            elo
                        ) SELECT
                            d_id,
                            '{ctx.guild.id}'
                            '{tog_game}',
                            {default_elo}
                        FROM (
                            SELECT DISTINCT s.discord_id AS d_id
                            FROM (
                                SELECT
                                    discord_id,
                                    game
                                FROM server_players
                                WHERE
                                    server_id='{ctx.guild.id}' AND
                                    is_member=true
                            ) AS s
                            WHERE
                                NOT EXISTS (
                                    SELECT *
                                    FROM s
                                    WHERE
                                        discord_id=d_id AND
                                        game='{tog_game}'
                                )
                        )
                    ;""")
                utils.database.commit()
                await self.rank_settings(ctx)

        games_str = ""
        for g in games:
            if len(games_str) > 0:
                games_str += '\n'
            games_str += g
        options = [
            ('Force Usernames', f_force_usernames, ('Enabled' if force_usernames else 'Disabled')),
            ('Games', f_games, games_str),
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

    async def rank_settings(self, ctx):
        """View and change settings for player and team ranking."""
        e = discord.Embed(title='Server Settings', description=ctx.author.mention, colour=discord.Colour.blue())
        e.set_footer(text='Rank Settings')
        utils.database.execute(f"""
            SELECT
                default_elo,
                elo_k_factor
            FROM servers
            WHERE server_id='{ctx.guild.id}'
        ;""")
        default_elo, k = utils.database.fetchone()
        async def f_default_elo(ctx):
            new_de = await utils.selectors.select_string(ctx, options=[1000, 1100, 1200, 1300, 1400, 1500], title='Server Settings', inst='Select a new default elo', footer='Default Elo')
            #don't continue if the selection has timed out
            if new_de != None:
                #only update settings if the new default is different from the old default
                if new_de != default_elo:
                    utils.database.execute(f"""
                        UPDATE servers
                        SET default_elo={new_de}
                        WHERE server_id='{ctx.guild.id}'
                    ;""")
                    utils.database.commit()
                await self.rank_settings(ctx)
        async def f_k_factor(ctx):
            new_k = await utils.selectors.select_string(ctx, options=[16, 24, 32, 64, 128], title='Server Settings', inst='Select a new k-factor value', footer='k-factor')
            #don't continue if the selection has timed out
            if new_k != None:
                #only update settings if the new k is different from the old k
                if new_k != k:
                    utils.database.execute(f"""
                        UPDATE servers
                        SET elo_k_factor={new_k}
                        WHERE server_id='{ctx.guild.id}'
                    ;""")
                    utils.database.commit()
                await self.rank_settings(ctx)
        options = [
            ('Default Elo', f_default_elo, f'{default_elo}'),
            ('k-factor', f_k_factor, f'{k}'),
            ('Back', self.settings_home, 'Return to the previous page')
        ]
        await self.menu_select(ctx, e, options)

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
