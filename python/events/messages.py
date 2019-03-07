import discord
from discord.ext import commands
from python import utils
import json

async def write_string(bot, msg):
    data = utils.cache.get('write_string', msg.channel.id)
    if data == None:
        return False
    author = data['author']
    if msg.author != author:
        return True
    written_string = msg.content
    data['done'](written_string)
    utils.cache.delete('write_string', msg.channel.id)
