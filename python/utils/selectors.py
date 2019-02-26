import discord
import asyncio
from python import utils

async def select_string(ctx, user, options, *, title='Select one', inst='Select an option'):
    #options should be a list of strings
    if len(options) == 0:
        return None
    if len(options) == 1:
        return options[0]
    e = discord.Embed(title=title, description=user.mention, colour=discord.Colour.blue())
    liststr = ""
    count = 0
    for o in options:
        if len(liststr) > 0:
            liststr += '\n'
        liststr += f"{utils.emoji_list[count]} {o}"
        count += 1
    e.add_field(name='inst', value=liststr)
    msg = await ctx.send(embed=e)
    for x in range(count):
        await msg.add_reaction(utils.emoji_list[x])
    selected_string = asyncio.get_event_loop().create_future()
    def done(choice):
        nonlocal selected_string
        selected_string.set_result(choice)
    utils.cache.add('select_string', msg.id, {'strings': options, 'author': user, 'done': done})
    try:
        await asyncio.wait_for(selected_string, timeout=60)
    except asyncio.TimoutError:
        e.clear_fields()
        e.add_field(name='Time expired', value='Selection timed out after 60 seconds.')
        await msg.edit(embed=e)
        utils.cache.delete('select_string', msg.id)
        return None
    return selected_string

async def select_team(ctx, user, team_list):
    #send a message to have the user select a team from a list
    #team_list should be a list of tuples: (team_id, team_name, game)
    if len(team_list) == 0:
        return None
    if len(team_list) == 1:
        return team_list[0][0]
    e = discord.Embed(title='Select Team', description=user.mention, colour=discord.Colour.blue())
    liststr = ""
    count = 0
    tids = []
    for team_id, team_name, game in team_list:
        tids.append(team_id)
        if len(liststr) > 0:
            liststr += '\n'
        liststr += f"{utils.emoji_list[count]} {team_name} **({game})**"
        count += 1
    e.add_field(name='Select a team', value=liststr)
    msg = await ctx.send(embed=e)
    for x in range(count):
        await msg.add_reaction(utils.emoji_list[x])
    selected_team = asyncio.get_event_loop().create_future()
    def done(team):
        nonlocal selected_team
        selected_team.set_result(team)
    utils.cache.add('select_team', msg.id, {'teams': tids, 'author': user, 'done': done})
    try:
        await asyncio.wait_for(selected_team, timeout=60)
    except asyncio.TimeoutError:
        e.clear_fields()
        e.add_field(name='Time expired', value='Selection timed out after 60 seconds.')
        await msg.edit(embed=e)
        utils.cache.delete('select_team', msg.id)
        return None
    return selected_team
