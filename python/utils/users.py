import discord
from python.utils import database
import json

def player_elo(discordid):
    database.execute(f"SELECT elo FROM player_table WHERE discord_id={discordid};")
    return database.fetchone()[0]
