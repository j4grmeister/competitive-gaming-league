import discord
from discord.ext import commands
from python import utils
from python.events import reactions
from python.events import messages

reaction_handlers = [
    reactions.team_invite,
    reactions.select_object
]

message_handlers = [
    messages.write_string
]

class Events:
    def __init__(self, bot):
        self.bot = bot

    async def on_message(self, msg):
        await self.bot.process_commands(msg)
        if user.id != self.bot.user.id:
            for handler in message_handlers:
                #only try handling again if the handle function returns false (indicating the reaction wasn't handled)
                if await handler(self.bot, msg):
                    break

    async def on_reaction_add(self, reaction, user):
        if user.id != self.bot.user.id:
            for handler in reaction_handlers:
                #only try handling again if the handle function returns false (indicating the reaction wasn't handled)
                if await handler(self.bot, reaction, user):
                    break

    async def on_guild_join(self, guild):
        utils.database.execute(f"""
            INSERT INTO servers (
                server_id
            ) VALUES (
                '{guild.id}'
            );""")
        utils.database.commit()

    async def on_member_join(self, member):
        guild = member.guild

        #get the server settings for this server
        utils.database.execute(f"""
            SELECT
                default_elo,
                games,
                team_roles_enabled,
                hoist_roles,
                mention_roles,
                force_usernames
            FROM servers
            WHERE server_id='{guild.id}'
        ;""")
        default_elo, games, team_roles_enabled, hoist_roles, mention_roles, force_usernames = utils.database.fetchone()

        #register the user in this league if they are registered with CGL
        #see if the user is registered with CGL (and get the data that we will need if they are)
        utils.database.execute(f"""
            SELECT username
            FROM players
            WHERE discord_id='{member.id}'
        ;""")
        username, = utils.database.fetchone()
        utils.database.execute(f"""
            SELECT
                teams.team_id,
                teams.game
            FROM teams
                INNER JOIN players
                ON teams.team_id=ANY(players.teams)
            WHERE
                players.discord_id='{member.id}'
        ;""")
        alldata = utils.database.fetchall()
        if username != None:
            if force_usernames:
                await member.edit(nick=username)
            #see if the user has already been a member of this server in the past
            utils.database.execute(f"""
                SELECT *
                FROM server_players
                WHERE
                    discord_id='{member.id}' AND
                    server_id='{guild.id}'
            ;""")
            if utils.database.fetchone() != None:
                #if they have been a member of this server before, then just update their is_member status and then move on
                utils.database.execute(f"""
                    UPDATE server_players
                    SET is_member=true
                    WHERE
                        discord_id='{member.id}' AND
                        server_id='{guild.id}'
                ;""")
            else:
                #create a new server_player entry for each game this server has
                for g in games:
                    utils.database.execute(f"""
                        INSERT INTO server_players (
                            discord_id,
                            server_id,
                            is_member,
                            elo,
                            game
                        ) VALUES (
                            '{member.id}',
                            '{guild.id}',
                            true,
                            {default_elo},
                            '{g}'
                    );""")
            #for each team that the player is on
            for team_id, g in alldata:
            #for g in games:
                if g in games:
                    #find if this team exists/is active in this server and get necessary data
                    utils.database.execute(f"""
                        SELECT
                            teams.team_name,
                            server_teams.role_id,
                            server_teams.team_elo,
                            teams.primary_players,
                            server_teams.primary_players,
                            server_teams.substitute_players
                        FROM server_teams
                            INNER JOIN teams
                            ON server_teams.team_id=teams.team_id
                        WHERE
                            server_teams.server_id='{guild.id}' AND
                            teams.team_id='{team_id}'
                    ;""")
                    team_name, role_id, team_elo, primary_players, s_primary_players, s_substitute_players = utils.database.fetchone()
                    #determine if this player is a primary player or a substitute
                    roster_field = 'substitute_players'
                    if str(member.id) in primary_players:
                        roster_field = 'primary_players'
                    #if this team doesn't exist on this server
                    if team_name == None:
                        #get the player's elo and determine the team elo for this server
                        utils.database.execute(f"""
                            SELECT elo
                            FROM server_players
                            WHERE
                                server_id='{guild.id}' AND
                                discord_id='{member.id}' AND
                                game='{g}'
                        ;""")
                        pelo, = utils.database.fetchone()
                        primaryq = utils.config.games[g]['primary_players']
                        telo = (default_elo * (primaryq - 1) + pelo) / primaryq
                        #create a new role if needed and give it to the player
                        troleid = '-1' #-1 means no role
                        if team_roles_enabled:
                            trole = await guild.create_role(name=team_name, colour=discord.Colour.orange(), hoist=hoist_roles, mentionable=mention_roles)
                            await member.add_roles(trole)
                            troleid = str(trole.id)
                        #create a new server team entry
                        utils.database.execute(f"""
                            INSERT INTO server_teams (
                                team_id,
                                server_id,
                                team_elo,
                                role_id,
                                {roster_field}
                            ) VALUES (
                                '{teams_id}',
                                '{guild.id}',
                                '{telo}',
                                '{troleid}',
                                '{{ "{member.id}" }}'
                            );""")
                    #if this team does exist on this server
                    else:
                        #determine if this team is active on this server
                        #this team is not active on this server
                        if len(s_primary_players) + len(s_substitute_players) == 0:
                            #get the player's elo and determine the team elo for this server
                            utils.database.execute(f"""
                                SELECT elo
                                FROM server_players
                                WHERE
                                    server_id='{guild.id}' AND
                                    discord_id='{member.id}' AND
                                    game='{g}'
                            ;""")
                            pelo, = utils.database.fetchone()
                            primaryq = utils.config.games[g]['primary_players']
                            telo = (default_elo * (primaryq - 1) + pelo) / primaryq
                            #create the team role if needed and give it to the player
                            troleid = '-1' #-1 means no role
                            if team_roles_enabled:
                                trole = await guild.create_role(name=team_name, colour=discord.Colour.orange(), hoist=hoist_roles, mentionable=mention_roles)
                                await member.add_roles(trole)
                                troleid = str(trole.id)

                            #update the team's server entry
                            utils.database.execute(f"""
                                UPDATE server_teams
                                SET
                                    role_id='{troleid}',
                                    team_elo={telo},
                                    {roster_field}='{{ \"{member.id}\" }}',
                                    is_active=true
                                WHERE
                                    server_id='{guild.id}' AND
                                    team_id='{teams_id}'
                            ;""")
                        #this team is active on this server
                        else:
                            #get the player's elo
                            utils.database.execute(f"""
                                SELECT elo
                                FROM server_players
                                WHERE
                                    server_id='{guild.id}' AND
                                    discord_id='{member.id}' AND
                                    game='{g}'
                            ;""")
                            p_elo, = utils.database.fetchone()
                            #calculate the new team elo for this server
                            team_size = len(s_primary_players) + len(s_substitute_players)
                            sum = team_elo * max(team_size, utils.config.games[game]['primary_players']) + p_elo
                            #if the teamsize is less than a full team, then the default elo is factored in for each missing player
                            #so subtract default elo once if needed since the new player replaces it
                            if team_size < utils.config.games[game]['primary_players']:
                                sum -= default_elo
                            #calculate the average
                            average = sum / max(team_size + 1, utils.config.games[game]['primary_players'])
                            #update this team's server entry
                            utils.database.execute(f"""
                                UPDATE server_teams
                                SET
                                    team_elo={average},
                                    {roster_field}=array_append({roster_field},
                                    '{member.id}')
                                WHERE
                                    server_id='{guild.id}' AND
                                    team_id='{team_id}'
                            ;""")
                            #add roles to this player if needed
                            if team_roles_enabled:
                                await member.add_roles(guild.get_role(int(role_id)))
            #commit database changes
            utils.database.commit()
        #TODO: record server growth stats

    async def on_member_remove(self, member):
        guild = member.guild

        #get the server settings for this server
        utils.database.execute(f"""
            SELECT
                default_elo,
                games
            FROM servers
            WHERE server_id='{guild.id}'
        ;""")
        default_elo, games = utils.database.fetchone()
        #see if this person is registered
        #utils.database.execute(f"""
        #    SELECT
        #        username,
        #        teams,
        #        elo
        #    FROM players
        #    WHERE discord_id='{member.id}'
        #;""")
        utils.database.execute(f"""
            SELECT
                teams.team_id,
                teams.game
            FROM teams
                INNER JOIN players
                ON teams.team_id=ANY(players.teams)
            WHERE
                players.discord_id='{member.id}'
        ;""")
        #username, teams = utils.database.fetchone()
        alldata = utils.database.fetchall()
        if alldata != None:
            #update the player's is_member status
            utils.database.execute(f"""
                UPDATE server_players
                SET is_member=false
                WHERE
                    discord_id='{member.id}' AND
                    server_id='{guild.id}'
            ;""")
            #if the player was on any teams team check the size of their server roster
            for team_id, g in alldata:
            #for g in games:
                if g in games:
                    utils.database.execute(f"""
                        SELECT
                            team_elo,
                            role_id,
                            primary_players,
                            substitute_players
                        FROM server_teams
                        WHERE
                            team_id='{team_id}' AND
                            server_id='{guild.id}'
                    ;""")
                    team_elo, role_id, primary_players, substitute_players = utils.database.fetchone()
                    #if the player was the last on their team, make the team inactive
                    if len(primary_players) + len(substitute_players) == 1:
                        utils.database.execute(f"""
                            UPDATE server_teams
                            SET
                                primary_players='{{}}',
                                substitute_players='{{}}',
                                team_elo={default_elo},
                                is_active=false
                            WHERE
                                team_id='{team_id}' AND
                                server_id='{guild.id}'
                        ;""")
                        #delete the team role if needed
                        if role_id != '-1':
                            await guild.get_role(int(role_id)).delete()
                    #otherwise just remove them from the server roster
                    else:
                        #get the player's elo
                        utils.database.execute(f"""
                            SELECT elo
                            FROM server_players
                            WHERE
                                discord_id='{member.id}' AND
                                server_id='{guild.id}' AND
                                game='{g}'
                        ;""")
                        pelo, = utils.database.fetchone()
                        #recalculate team elo
                        team_size = len(primary_players) + len(substitute_players)
                        primaryq = utils.config.games[g]['primary_players']
                        sum = team_elo * max(team_size, primaryq) - pelo
                        if team_size <= primaryq:
                            sum += default_elo
                        average = sum / max(team_size - 1, primaryq)
                        #update the team's server entry
                        utils.database.execute(f"""
                            UPDATE server_teams
                            SET
                                team_elo={average},
                                primary_players=array_remove(primary_players, '{member.id}'),
                                substitute_players=array_remove(substitute_players, '{member.id}')
                            WHERE
                                team_id='{team_id}' AND
                                server_id='{guild.id}'
                        ;""")
        #commit database changes
        utils.database.commit()

        #TODO: record server growth stats

    async def on_guild_role_delete(self, role):
        guild = role.guild
        #TODO: recreate roles when deleted

def setup(bot):
    bot.add_cog(Events(bot))
