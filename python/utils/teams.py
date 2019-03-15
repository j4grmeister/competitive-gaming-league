import discord
from python.utils import database
from python import utils

def get_owned_teams(guild_id, user_id):
    database.execute(f"""
        SELECT team_id
        FROM teams
        WHERE
            owner_id='{user_id}' AND
            game=ANY(
                SELECT UNNEST(games) AS games
                FROM servers
                WHERE server_id='{guild_id}'
    );""")
    teams = database.fetchall()
    r = []
    for t, in teams:
        r.append(t)
    return r

def team_name(team_id):
    database.execute(f"""
        SELECT team_name
        FROM teams
        WHERE team_id='{team_id}'
    ;""")
    return database.fetchone()[0]

def team_game(team_id):
    database.execute(f"""
        SELECT game
        FROM teams
        WHERE team_id='{team_id}'
    ;""")
    return database.fetchone()[0]

def primary_players(team_id):
    database.execute(f"""
        SELECT primary_players
        FROM teams
        WHERE team_id='{team_id}'
    ;""")
    return database.fetchone()[0]

def substitute_players(team_id):
    database.execute(f"""
        SELECT sub_players
        FROM teams
        WHERE team_id='{team_id}'
    ;""")
    return database.fetchone()[0]

async def disband_team(team_id):
    pass
