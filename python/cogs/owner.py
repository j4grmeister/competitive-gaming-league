import discord
from discord.ext import commands
from python import utils

class Owner:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def settings(self, ctx):
        e = discord.Embed(title='Server Settings', description=ctx.author.mention, colour=discord.Colour.blue())
        e.set_footer(text='Home')
        e.add_field(name=f'{utils.emoji_list[0]} Ranking Settings', value=self.ranking_settings.__doc__)
        await (await utils.selectors.select_object(ctx, objects=[self.ranking_settings, 'test'], embed=e))(ctx)

    async def ranking_settings(self, ctx):
        e = discord.Embed(title='Server Settings', description=ctx.author.mention, colour=discord.Colour.blue())
        e.set_footer(text='Ranking Settings')
        e.add_field(name='test', value='test')
        await ctx.send(embed=e)

    @commands.command(pass_context=True)
    #@utils.checks.server_owner()
    async def setting(self, ctx, key, *, value):
        utils.database.execute(f"UPDATE servers SET {key}={value} WHERE server_id='{ctx.guild.id}';")
        utils.database.commit()
        await ctx.send("Setting has been updated.")

    @commands.command(pass_context=True)
    async def reset(self, ctx):
        utils.database.execute("DELETE FROM players;")
        utils.database.execute("DELETE FROM teams;")
        utils.database.execute("DELETE FROM server_players;")
        utils.database.execute("DELETE FROM server_teams;")
        utils.database.commit()
        await ctx.send("Database reset")

def setup(bot):
    bot.add_cog(Owner(bot))
