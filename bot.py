import discord
from discord.ext import commands
import os
import python.cogs
import python.events
import python.utils

extensions = [
    'python.cogs.general',
    'python.cogs.teams',
    'python.cogs.owner',
    'python.events.events',
    'python.utils.guilds',
    'python.events.events'
]

bot = commands.Bot(command_prefix='!')

if __name__ == '__main__':
    for ext in extensions:
        try:
            bot.load_extension(ext)
        except Exception as e:
            print(f"failed to load extension {ext}.\n" + str(e))

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

    bot.appinfo = await bot.application_info()

token = os.environ['DISCORD_TOKEN']
bot.run(token)
