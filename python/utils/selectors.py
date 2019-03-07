import discord
import asyncio
from python import utils

async def select_object(ctx, *, objects=[], embed=None, select_multiple=False, timeout=60):
    if len(objects) == 0:
        return None
    if len(objects) == 1:
        return objects[0]
    msg = await ctx.send(embed=embed)
    for x in range(len(objects)):
        await msg.add_reaction(utils.emoji_list[x])
    if select_multiple:
        await msg.add_reaction(utils.emojie_confirm)
    selected_object = asyncio.get_event_loop().create_future()
    def done(index):
        nonlocal selected_object
        if select_multiple:
            selected_object.set_result([objects[i] for i in index])
        else:
            selected_object.set_result(objects[index])
    utils.cache.add('select_object', msg.id, {'author': ctx.author, 'done': done, 'select_multiple': select_multiple})
    try:
        await asyncio.wait_for(selected_object, timeout=timeout)
    except asyncio.TimeoutError:
        embed.clear_fields()
        embed.add_field(name='Time expired', value=f'Response timed out after {timeout} seconds.')
        await msg.edit(embed=embed)
        utils.cache.delete('select_object', msg.id)
        return None
    return selected_object.result()

async def select_string(ctx, *, options=[], select_multiple=False, title='Select one', inst='Select an option', timeout=60):
    #options should be a list of strings
    if len(options) == 0:
        return None
    if len(options) == 1:
        return options[0]
    e = discord.Embed(title=title, description=ctx.author.mention, colour=discord.Colour.blue())
    liststr = ""
    count = 0
    for o in options:
        if len(liststr) > 0:
            liststr += '\n'
        liststr += f"{utils.emoji_list[count]} {o}"
        count += 1
    e.add_field(name=inst, value=liststr)
    return await select_object(ctx, objects=options, embed=e, select_multiple=select_multiple, timeout=timeout)

async def select_team(ctx, *, teams=[], title='Select Team', inst='Select a team', select_multiple=False, timeout=60):
    #send a message to have the user select a team from a list
    #teams should be a list of tuples: (team_id, team_name, game)
    if len(teams) == 0:
        return None
    if len(teams) == 1:
        return teams[0][0]
    e = discord.Embed(title=title, description=ctx.author.mention, colour=discord.Colour.blue())
    liststr = ""
    count = 0
    tids = []
    for team_id, team_name, game in teams:
        tids.append(team_id)
        if len(liststr) > 0:
            liststr += '\n'
        liststr += f"{utils.emoji_list[count]} {team_name} **({game})**"
        count += 1
    e.add_field(name=inst, value=liststr)
    return await select_object(ctx, *, objects=tids, embed=e, select_multiple=select_multiple, timeout=timeout)

async def write_string(ctx, *, title='Write Something', name='Write', inst='Write anything', timeout=60):
    e = discord.Embed(title=title, description=ctx.author.mention, colour=discord.Colour.blue())
    e.add_field(name=name, value=inst)
    msg = await ctx.send(embed=e)
    written_string = asyncio.get_event_loop().create_future()
    def done(string):
        nonlocal written_string
        written_string.set_result(string)
    utils.cache.add('write_string', ctx.channel.id, {'author': ctx.author, 'done': done})
    try:
        await asyncio.wait_for(written_string, timeout=timeout)
    except asyncio.TimeoutError:
        e.clear_fields()
        e.add_field(name='Time expired', value=f'Response timed out after {timeout} seconds.')
        await msg.edit(embed=e)
        utils.cache.delete('write_string', ctx.channel.id)
        return None
    return written_string.result()
