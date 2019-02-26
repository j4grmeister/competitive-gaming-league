import discord
import asyncio
from python import utils

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
    selected_team = None
    def done(team):
        nonlocal selected_team
        selected_team = team
    utils.cache.add('select_team', msg.id, {'teams': tids, 'author': user, 'done': done})
    time = 0
    while selected_team == None:
        await asyncio.sleep(1)
        time += 1
        #timeout after 60 seconds
        if time >= 60:
            e.clear_fields()
            e.add_field(name='Timed Out', value='Team selection timed out after 60 seconds.\nTry again.')
            await msg.edit(embed=e)
            utils.cache.delete('select_team', msg.id)
            return None
    return selected_team