import discord
from discord.ext import commands
from python import utils
import json

async def set_region(bot, reaction, user):
    print('set region')
    msg = reaction.message
    target_userid = utils.cache.get('set_region_message', msg.id)
    if target_userid == None:
        return False
    if target_userid != user.id:
        return True
    member_region = ""
    if reaction.emoji == '🇺🇸':
        member_region = "NA"
    elif reaction.emoji == '🇪🇺':
        member_region = "EU"
    else:
        return True
    utils.database.execute(f"UPDATE player_table SET region='{member_region}' WHERE discord_id={target_userid};")
    #grant region roles in all servers
    utils.database.execute(f"SELECT server_id, region_roles -> '{member_region}' FROM server_table WHERE region_roles_enabled=TRUE;")
    serverlist = utils.database.fetchall()
    for sid, role in serverlist:
        guild = bot.get_guild(sid)
        member = guild.get_member(user.id)
        await member.add_roles(guild.get_role(role))
    utils.cache.delete('set_region_message', msg.id)
    utils.database.commit()
    await msg.delete()
    await msg.channel.send("Your region has been updated.")
    return True

async def get_roles(bot, reaction, user):
    msg = reaction.message
    guild = msg.guild
    target_userid = utils.cache.get('get_roles_message', msg.id)
    if target_userid == None:
        return False
    if target_userid != user.id:
        return True
    if reaction.emoji != utils.emoji_confirm:
        return True
    server_roles = json.loads(utils.database.server_setting(ctx.guild.id, 'requestable_roles'))
    #not sure if this little bit works
    utils.database.execute(f"SELECT server_roles -> '{guild.id}' FROM player_table WHERE discord_id={user.id};")
    member_roles = json.loads(utils.database.fetchone()[0])
    #end of uncertainty
    allreactions = msg.reactions
    for r in allreactions:
        if r.emoji in utils.emoji_list:
            users = await r.users().flatten()
            user_reacted = (next((u for u in users if u.id == target_userid), None) != None)
            bot_reacted = (next((u for u in users if u.id == bot.user.id), None) != None)
            if user_reacted and bot_reacted:
                index = utils.emoji_list.index(r.emoji)
                roleid = list(server_roles.values())[index]
                if roleid in member_roles:
                    await user.remove_roles(guild.get_role(roleid))
                else:
                    await user.add_roles(guild.get_role(roleid))
    utils.cache.delete('get_roles_message', msg.id)
    utils.database.commit()
    await msg.delete()
    await msg.channel.send("Your roles have been updated.")
    return True

async def create_team(bot, reaction, user):
    msg = reaction.message
    cached_data = utils.cache.get('create_team_message', msg.id)
    if cached_data == None:
        return False
    target_userid = cached_data['user']
    if target_userid != user.id:
        return True
    game = ""
    guild_games = cached_data['guild_games']
    if reaction.emoji in utils.emoji_list:
        bot_reacted = (next((u for u in users if u.id == bot.user.id), None) != None)
        if bot_reacted:
            index = utils.emoji_list.index(reaction.emoji)
            game = guild_games[index]
        else:
            return True
    else:
        return True
    team_name = cached_data['team_name']
    #check that the player isnt already on a team for this server's game
    utils.database.execute(f"SELECT teams -> '{game}' FROM player_table WHERE discord_id={target_userid};")
    player_team = utils.database.fetchone()[0]
    if player_team != None:
        await ctx.send(f"You are already on a {game} team.\nYou cannot be on more than one team per game.")
        return
    #generate an id for the team
    teamid = utils.generate_id()
    #escape the team name to prevent SQL injection
    eteam_name = utils.security.escape_sql(team_name)
    #get all the servers that the player is in that have this game as their primary game
    #create team roles as well
    team_elo = {}
    utils.database.execute(f"SELECT server_id, team_roles_enabled, default_role, hoist_roles, mention_roles FROM server_table WHERE '{game}'=ANY(games);")
    allservers = utils.database.fetchall()
    for sid, team_roles_enabled, default_role, hoist_roles, mention_roles in allservers:
        guild = bot.get_guild(sid)
        member = guild.get_member(target_userid)
        if member != None:
            utils.database.execute(f"SELECT elo -> '{guild.id}' FROM player_table WHERE discord_id={target_userid};")
            team_elo[f"{sid}"] = utils.database.fetchone()[0]
            troleid = '0' #0 means no role
            if team_roles_enabled:
                drole = guild.get_role(default_role)
                await member.remove_roles(drole)
                trole = await guild.create_role(name=team_name, permissions=drole.permissions, colour=discord.Colour.orange(), hoist=hoist_roles, mentionable=mention_roles)
                await member.add_roles(trole)
                troleid = trole.id
            utils.database.execute(f"UPDATE server_table SET teams=teams::jsonb || '{{\"{teamid}\": {troleid}}}'::jsonb WHERE server_id={sid};")
    #create the team's database entry
    utils.database.execute(f"INSERT INTO team_table (owner_id, team_id, game, team_name, team_elo, primary_players) VALUES ({target_userid}, {teamid}, '{game}', '{eteam_name}', '{json.dumps(team_elo)}', '{{{target_userid}}}');")
    #add the user to the team
    utils.database.execute(f"UPDATE player_table SET teams=teams::jsonb || '{{\"{guild_games[0]}\": {teamid}}}'::jsonb WHERE discord_id={target_userid};")
    #commit changes
    utils.database.commit()
    utils.cache.delete('create_team_message', msg.id)
    await msg.delete()
    await ctx.send("Your team has been created.")
    return True

async def change_team_name(bot, reaction, user):
    msg = reaction.message
    cached_data = utils.cache.get('change_team_name_message', msg.id)
    if cached_data == None:
        return False
    target_userid = cached_data['user']
    if target_userid != user.id:
        return True
    owned_teams = cached_data['owned_teams']
    owned_team = None
    if reaction.emoji in utils.emoji_list:
        bot_reacted = (next((u for u in users if u.id == bot.user.id), None) != None)
        if bot_reacted:
            index = utils.emoji_list.index(reaction.emoji)
            owned_team = owned_teams[index]
        else:
            return True
    else:
        return True
    team_name = cached_data['team_name']

    utils.database.execute("SELECT server_id, teams FROM server_table WHERE team_roles_enabled=TRUE;")
    allservers = utils.database.fetchall()
    for sid, teams_json in allservers:
        teams = json.loads(teams_json)
        if owned_teams[0] in teams:
            guild = bot.get_guild(sid)
            role = guild.get_role(teams[owned_team])
            await role.edit(name=team_name)
    eteam_name = utils.security.escape_sql(team_name)
    utils.database.execute(f"UPDATE team_table SET team_name='{eteam_name}' WHERE team_id={owned_team};")
    utils.database.commit()
    utils.cache.delete('change_team_name_message', msg.id)
    await msg.delete()
    await ctx.send("Your team name has been changed.")

async def team_invite(bot, reaction, user):
    msg = reaction.message
    team_id = utils.cache.get('team_invite_message', msg.id)
    if team_id == None:
        return False
    if reaction.emoji == utils.emoji_decline:
        await msg.delete()
        utils.cache.delete('team_invite_message', msg.id)
        return True
    if reaction.emoji == utils.emoji_confirm:
        game = utils.teams.team_game(team_id)
        #check that the player is not already on a team for this game
        utils.database.execute(f"SELECT teams -> '{game}' FROM player_table WHERE discord_id={user.id};")
        player_team = utils.database.fetchone()[0]
        if player_team != None:
            await msg.delete()
            utils.cache.delete('team_invite_message', msg.id)
            await ctx.send(f"You are already on a {game} team.\nYou cannot be on more than one team per game.")
            return True
        max_primary = utils.config.games[game]['primary_players']
        primary = len(utils.teams.primary_players(team_id))
        subs = len(utils.teams.substitute_players(team_id))
        teamsize = primary + subs
        is_primary = (primary + 1 <= max_primary)
        utils.database.execute(f"UPDATE player_table SET teams=teams::jsonb || '{{\"{game}\": {team_id}}}'::jsonb WHERE discord_id={user.id};")
        #TODO: iterate through servers with the team in them instead of iterating through servers the team has an elo setting for
        team_elo = utils.teams.team_elo(team_id)
        player_elo = utils.teams.player_elo(user.id)
        for server in team_elo:
            before_elo = team_elo[server]
            utils.database.execute(f"SELECT default_elo FROM server_table WHERE server_id={server};")
            p_elo = utils.database.fetchone()[0]
            if server in player_elo:
                p_elo = player_elo[server]
            else:
                #TODO: turn this into a single SQL query
                utils.database.execute(f"UPDATE player_table SET elo=elo::jsonb || '{{\"{server}\": {p_elo}}}'::jsonb WHERE discord_id={user.id};")
            after_elo = (before_elo * teamsize + utils.users.team) / teamsize + 1
            team_elo[server] = after_elo
        if is_primary:
            utils.database.execute(f"UPDATE team_table SET primary=array_append(primary, {user.id}), team_elo=team_elo::jsonb || '{json.dumps(team_elo)}'::jsonb WHERE team_id={team_id};")
        else:
            utils.database.execute(f"UPDATE team_table SET subs=array_append(subs, {user.id}), team_elo=team_elo::jsonb || '{json.dumps(team_elo)}'::jsonb WHERE team_id={team_id};")
        utils.database.commit()
        await msg.delete()
        utils.cache.delete('team_invite_message', msg.id)
        await ctx.send(f"You have joined {utils.teams.team_name(team_id)}.")
        return True
    return True

async def invite_to_team(bot, reaction, user):
    msg = reaction.message
    cached_data = utils.cache.get('invite_to_team_message', msg.id)
    target_user = cached_data['user']
    author = cached_data['author']
    if author.id != user.id:
        return True
    owned_teams = cached_data['owned_teams']
    owned_team = None
    if reaction.emoji in utils.emoji_list:
        bot_reacted = (next((u for u in users if u.id == bot.user.id), None) != None)
        if bot_reacted:
            index = utils.emoji_list.index(reaction.emoji)
            owned_team = owned_teams[index]
        else:
            return True
    else:
        return True
    #check that the player is not already on a team for this game
    game = utils.teams.team_game(owned_teams[0])
    utils.database.execute(f"SELECT teams -> '{game}' FROM player_table WHERE discord_id={target_user.id};")
    player_team = utils.database.fetchone()[0]
    if player_team != None:
        await msg.delete()
        utils.cache.delete('invite_to_team_message', msg.id)
        await ctx.send(f"That player is already on a {game} team.\nYou cannot be on more than one team per game.")
        return True
    team_name = cached_data['team_name']
    e = discord.Embed(title="Team invite", description=f"From {author.mention}", colour=discord.Colour.blue())
    e.add_field(name=f"You have been invited to {team_name};", value=f"React with {utils.emoji_confirm} to accept or {utils.emoji_decline} to decline.")
    nmsg = await target_user.send(embed=e)
    await nmsg.add_reaction(utils.emoji_confirm)
    await nmsg.add_reaction(utils.emoji_decline)
    utils.cache.add('team_invite_message', nmsg.id, owned_team)
    await msg.channel.send(f"{username} has been invited to {team_name}.")
    utils.cache.delete('invite_to_team_message', msg.id)
    await msg.delete()
    return True
