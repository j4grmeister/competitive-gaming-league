import discord
import database
import json

def player_elo(discordid):
    database.execute(f"SELECT elo FROM team_table WHERE team_id={team_id};")
    return json.loads(database.fetchone()[0])
