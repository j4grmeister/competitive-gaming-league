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
        #determine if the player is automatically a primary player
        max_primary = utils.config.games[game]['primary_players']
        primary = len(utils.teams.primary_players(team_id))
        is_primary = (primary + 1 <= max_primary)
        roster_field = "substitute_players"
        if is_primary:
            roster_field = "primary_players"
        #add the team to the player's database entry
        utils.database.execute(f"UPDATE players SET teams=teams::jsonb || '{{ \"{game}\": \"{team_id}\" }}'::jsonb WHERE discord_id='{user.id}';")
        #add the player to the team's roster
        utils.database.execute(f"UPDATE teams SET {roster_field}=array_append({roster_field}, '{user.id}') WHERE team_id='{team_id}';")
        #get all the servers that the player is a member of in that the team is also registered in
        utils.database.execute(f"""SELECT server_teams.server_id, server_teams.role_id, server_teams.team_elo, server_players.elo, server_teams.primary_players, server_teams.substitute_players
            FROM server_teams
            INNER JOIN server_players ON server_teams.server_id=server_players.server_id
            WHERE server_players.discord_id='{user.id}' AND server_players.is_member=true;""")
        allservers = utils.database.fetchall()
        for sid, role_id, before_elo, p_elo, pri, subs in allservers:
            #assign team roles if needed
            if role_id != '-1':
                await user.add_roles(msg.guild.get_role(int(role_id)))
            #calculate the new team elo for this server
            team_size = len(pri) + len(subs)
            sum = before_elo * max(team_size, utils.config.games[game]['primary_players']) + p_elo
            #if the teamsize is less than a full team, then the default elo is factored in for each missing player
            #so subtract default elo once if needed since the new player replaces it
            if team_size < utils.config.games[game]['primary_players']:
                #get the default elo for this server
                utils.database.execute(f"SELECT default_elo FROM servers WHERE server_id='{sid}';")
                default_elo, = utils.database.fetchone()
                sum -= default_elo
            #calculate the average
            average = sum / max(team_size + 1, utils.config.games[game]['primary_players'])
            #update the new elo value and add the player to the team roster on this server
            utils.database.execute(f"UPDATE server_teams SET team_elo={average}, {roster_field}=array_append({roster_field}, '{user.id}') WHERE team_id='{team_id}' AND server_id='{sid}';")
        #commit database changes
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
        users = await reaction.users().flatten()
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
    users = await reaction.users().flatten()
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
