import discord
from discord.ext import commands
import os
import python.cogs
import python.events
import python.utils

extensions = [
    'python.cogs.general',
    'python.cogs.teams',
    'python.cogs.stats',
    'python.cogs.admin',
    'python.cogs.owner',
    'python.events.events',
    'python.events.events'
]

bot = commands.Bot(command_prefix='!')

if __name__ == '__main__':
    for ext in extensions:
        try:
            bot.load_extension(ext)
        except Exception as e:
            print(f"failed to load extension {ext}.\n" + str(e))

#To whomever may read or edit any code contained in this project,
#I apologize.
#-Nick Greene

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    listen_act = discord.Activity(name='!help', type=discord.ActivityType.listening)
    await bot.change_presence(activity=listen_act)
    bot.appinfo = await bot.application_info()

token = os.environ['DISCORD_TOKEN']
bot.run(token)
