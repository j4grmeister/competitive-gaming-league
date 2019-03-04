import discord
from python.utils import database
import json

def username(discordid):
    database.execute(f"""
        SELECT username
        FROM players
        WHERE discord_id='{discordid}'
    ;""")
    return database.fetchone()[0]
