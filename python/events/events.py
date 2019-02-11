import discord
from discord.ext import commands
from python import utils
from python.events import reactions

reaction_handlers = [
    reactions.set_region,
    reactions.get_roles,
    reactions.create_team,
    reactions.change_team_name,
    reactions.team_invite,
    reactions.invite_to_team
]

class Events:
    def __init__(self, bot):
        self.bot = bot

    async def on_reaction_add(self, reaction, user):
        if user.id != self.bot.user.id:
            for handler in reaction_handlers:
                #only try handling again if the handle function returns false (indicating the reaction wasn't handled)
                if await handler(self.bot, reaction, user):
                    break

    async def on_guild_join(self, guild):
        utils.database.execute(f"INSERT INTO server_table (server_id) VALUES ({guild.id});")
        utils.database.commit()

    async def on_member_join(self, member):
        guild = member.guild
        #register the member in this league if they are registered with cgl
        utils.database.execute(f"SELECT * FROM player_table WHERE discord_id={member.id};")
        if utils.database.fetchone() != None:
            utils.database.execute(f"SELECT default_elo, force_usernames, team_roles_enabled, region_roles_enabled FROM server_table WHERE server_id={guild.id};")
            default_elo, force, roles, region = utils.database.fetchone()
            utils.database.execute(f"UPDATE player_table SET elo=elo | '{{{guild.id}: {default_elo}}}' WHERE discord_id={member.id};")
            utils.database.execute(f"UPDATE player_table SET server_roles=server_roles || '{{{guild.id}: []}}' WHERE discord_id={member.id};")
            if force:
                await member.edit(nick=utils.database.player_setting(member.id, 'username'))
            if roles:
                teamid = utils.database.player_setting(member.id, 'team_id')
                if teamid == None:
                    await member.add_roles(guild.get_role(utils.database.server_setting(guild.id, 'default_role')))
                #TODO: add/create team role if player is on a team
            if region:
                member_region = utils.database.player_setting(member.id, 'region')
                utils.database.execute(f"SELECT region_roles -> '{member_region}' from server_table WHERE server_id={guild.id};")
                region_role = utils.database.fetchone()[0]
                await member.add_roles(guild.get_role(region_role))
            utils.database.commit()
        #TODO: record server growth stats

    async def on_member_remove(self, member):
        pass
        #TODO: record server growth stats
        #TODO: remove unused roles

    async def on_guild_role_delete(self, role):
        guild = role.guild
        #TODO: recreate roles when deleted

def setup(b):
    bot.add_cog(Events(bot))
