import discord
import asyncio
from python import utils

async def select_object(ctx, *, objects=[], embed=None, select_multiple=False, timeout=60):
    if len(objects) == 0:
        return None
    if len(objects) == 1:
        return objects[0]
    msg = await ctx.send(embed=embed)
    selected_object = asyncio.get_event_loop().create_future()
    def done(index):
        nonlocal selected_object
        if select_multiple:
            selected_object.set_result([objects[i] for i in index])
        else:
            selected_object.set_result(objects[index])
    utils.cache.add('select_object', msg.id, {'author': ctx.author, 'done': done, 'select_multiple': select_multiple})
    for x in range(len(objects)):
        print(msg)
        await msg.add_reaction(utils.emoji_list[x])
    if select_multiple:
        await msg.add_reaction(utils.emoji_confirm)
    try:
        await asyncio.wait_for(selected_object, timeout=timeout)
    except asyncio.TimeoutError:
        embed.clear_fields()
        embed.add_field(name='Time expired', value=f'Response timed out after {timeout} seconds.')
        await msg.edit(embed=embed)
        utils.cache.delete('select_object', msg.id)
        return None
    return selected_object.result()

async def select_emoji(ctx, *, options=[], embed=None, timeout=60):
    if len(options) == 0:
        return None
    if len(options) == 1:
        return options[0]
    msg = await ctx.send(embed=embed)
    selected_emoji = asyncio.get_event_loop().create_future()
    def done(emoji):
        nonlocal selected_emoji
        selected_emoji = emoji
    utils.cache.add('select_emoji', msg.id, {'author': ctx.author, 'done': done})
    for e in options:
        await msg.add_reaction(e)
    try:
        await asyncio.wait_for(selected_emoji, timeout=timeout)
    except asyncio.TimeoutError:
        embed.clear_fields()
        embed.add_field(name='Time expired', value=f'Response timed out after {timeout} seconds.')
        print(msg)
        await msg.edit(embed=embed)
        utils.cache.delete('select_emoji', msg.id)
        return None
    return selected_emoji.result()

async def confirm(ctx, *, title='Some Category, idk', warning='Are you sure?', message='you don\'t want to do this', footer=None, timeout=60):
    e = discord.Embed(title=title, description=ctx.author.mention, colour=discord.Colour.blue())
    if footer != None:
        e.set_footer(text=footer)
    e.add_field(name=warning, value=message)
    selected_emoji = await select_emoji(ctx, options=[utils.emoji_decline, utils.emoji_confirm], embed=e, timeout=timeout)
    if selected_emoji == None:
        return False
    return (selected_emoji == utils.emoji_confirm)

async def select_string(ctx, *, options=[], title='Select one', inst='Select an option', footer=None, select_multiple=False, timeout=60):
    #options should be a list of strings
    if len(options) == 0:
        return None
    if len(options) == 1:
        return options[0]
    e = discord.Embed(title=title, description=ctx.author.mention, colour=discord.Colour.blue())
    if footer != None:
        e.set_footer(text=footer)
    liststr = ""
    count = 0
    for o in options:
        if len(liststr) > 0:
            liststr += '\n'
        liststr += f"{utils.emoji_list[count]} {o}"
        count += 1
    e.add_field(name=inst, value=liststr)
    return await select_object(ctx, objects=options, embed=e, select_multiple=select_multiple, timeout=timeout)

async def select_team(ctx, *, teams=[], title='Select Team', inst='Select a team', footer=None, select_multiple=False, timeout=60):
    #send a message to have the user select a team from a list
    #teams should be a list of tuples: (team_id, team_name, game)
    if len(teams) == 0:
        return None
    if len(teams) == 1:
        return teams[0][0]
    e = discord.Embed(title=title, description=ctx.author.mention, colour=discord.Colour.blue())
    if footer != None:
        e.set_footer(text=footer)
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
    return await select_object(ctx, objects=tids, embed=e, select_multiple=select_multiple, timeout=timeout)
