import discord
from discord.ext import commands
from python import utils
import json

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
    if cached_data['select_multiple']:
        if reaction.emoji != utils.emoji_confirm:
            return True
        selected_string = []
        for r in reaction.message.reactions:
            if r.emoji in utils.emoji_list:
                bot_reacted = (next((u for u in users if u.id == bot.user.id), None) != None)
                user_reacted = (next((u for u in users if u.id == target_userid), None) != None)
                if bot_reacted and user_reacted:
                    index = utils.emoji_list.index(r.emoji)
                    selected_string.append(options[index])
        return True
    else:
        selected_string = None
        users = reaction.users.flatten()
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
