import discord
from discord.ext import commands
from python import utils
import json

async def set_region(bot, reaction, user):
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
    utils.database.execute(f"UPDATE players SET region='{member_region}' WHERE discord_id='{target_userid}';")
    #grant region roles in all servers
    utils.database.execute(f"SELECT server_id, region_roles -> '{member_region}' FROM servers WHERE region_roles_enabled=TRUE;")
    serverlist = utils.database.fetchall()
    for sid, role in serverlist:
        guild = bot.get_guild(int(sid))
        member = guild.get_member(user.id)
        await member.add_roles(guild.get_role(int(role)))
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
    server_roles = json.loads(utils.database.server_setting(msg.channel.guild.id, 'requestable_roles'))
    #not sure if this little bit works
    utils.database.execute(f"SELECT server_roles -> '{guild.id}' FROM players WHERE discord_id='{user.id}';")
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

    utils.database.execute("SELECT server_id, teams FROM servers WHERE team_roles_enabled=TRUE;")
    allservers = utils.database.fetchall()
    for sid, teams_json in allservers:
        teams = json.loads(teams_json)
        if owned_teams[0] in teams:
            guild = bot.get_guild(int(sid))
            role = guild.get_role(int(teams[owned_team]))
            await role.edit(name=team_name)
    eteam_name = utils.security.escape_sql(team_name)
    utils.database.execute(f"UPDATE teams SET team_name='{eteam_name}' WHERE team_id='{owned_team}';")
    utils.database.commit()
    utils.cache.delete('change_team_name_message', msg.id)
    await msg.delete()
    await msg.channel.send("Your team name has been changed.")

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
        utils.database.execute(f"SELECT teams -> '{game}' FROM players WHERE discord_id='{user.id}';")
        player_team = utils.database.fetchone()[0]
        if player_team != None:
            await msg.delete()
            utils.cache.delete('team_invite_message', msg.id)
            await msg.channel.send(f"You are already on a {game} team.\nYou cannot be on more than one team per game.")
            return True
        max_primary = utils.config.games[game]['primary_players']
        primary = len(utils.teams.primary_players(team_id))
        subs = len(utils.teams.substitute_players(team_id))
        teamsize = primary + subs
        is_primary = (primary + 1 <= max_primary)
        utils.database.execute(f"UPDATE players SET teams=teams::jsonb || '{{ \"{game}\": \"{team_id}\" }}'::jsonb WHERE discord_id='{user.id}';")
        #TODO: iterate through servers with the team in them instead of iterating through servers the team has an elo setting for
        utils.database.execute(f"SELECT server_id, team_elo FROM server_teams WHERE team_id='{team_id}';")
        servers = utils.database.fetchall()
        for server_id, before_elo in allservers:
            utils.database.execute(f"SELECT default_elo, games FROM servers WHERE server_id='{server_id}';")
            p_elo, games = utils.database.fetchone()
            utils.database.execute(f"SELECT discord_id FROM server_players WHERE server_id='{server_id}';")
            if utils.database.fetchone() != None:
                utils.database.execute(f"SELECT elo FROM server_players WHERE server_id='{server_id}' AND discord_id='{user.id}' AND game='{game}';")
                p_elo, = utils.database.fetchone()
            else:
                #TODO: turn this into a single SQL query
                for g in games:
                    utils.database.execute(f"INSERT INTO server_players (discord_id, server_id, game, elo) VALUES ('{user.id}', '{server_id}', '{g}', {p_elo});")
            after_elo = (before_elo * teamsize + p_elo) / teamsize + 1
            team_elo[server] = after_elo
        if is_primary:
            utils.database.execute(f"UPDATE teams SET primary_players=array_append(primary_players, '{user.id}'), team_elo=team_elo::jsonb || '{json.dumps(team_elo)}'::jsonb WHERE team_id='{team_id}';")
        else:
            utils.database.execute(f"UPDATE teams SET substitute_players=array_append(substitute_players, '{user.id}'), team_elo=team_elo::jsonb || '{json.dumps(team_elo)}'::jsonb WHERE team_id='{team_id}';")
        utils.database.commit()
        await msg.delete()
        utils.cache.delete('team_invite_message', msg.id)
        await msg.channel.send(f"You have joined {utils.teams.team_name(team_id)}.")
        return True
    return True

async def select_string(bot, reaction, user):
    #get the string that was selected
    msg = reaction.message
    cached_data = utils.cache.get('select_string', msg.id)
    if cached_data == None:
        return False
    author = cached_data['author']
    if author.id != user.id:
        return True
    options = cached_data['options']
    selected_string = None
    bot_reacted = (next((u for u in users if u.id == bot.user.id), None) != None)
    if bot_reacted:
        index = utils.emoji_list.index(reaction.emoji)
        selected_string = options[index]
    else:
        return True
    #continue execution of the thread that requested the selection
    cached_data['done'](selected_string)
    utils.cache.delete('select_team', msg.id)
    await msg.delete()
    return True

async def select_team(bot, reaction, user):
    #get the team that was selected
    msg = reaction.message
    cached_data = utils.cache.get('select_team', msg.id)
    if cached_data == None:
        return False
    author = cached_data['author']
    if author.id != user.id:
        return True
    teams = cached_data['teams']
    selected_team = None
    bot_reacted = (next((u for u in users if u.id == bot.user.id), None) != None)
    if bot_reacted:
        index = utils.emoji_list.index(reaction.emoji)
        selected_team = teams[index]
    else:
        return True
    #continue execution of the thread that requested the selection
    cached_data['done'](selected_team)
    utils.cache.delete('select_team', msg.id)
    await msg.delete()
    return True
