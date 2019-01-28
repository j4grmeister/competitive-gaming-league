import discord
import python.utils.database
import json

def get_owned_teams(guild_id, user_id):
    database.execute(f"SELECT team_id FROM team_table WHERE owner_id={user_id} AND game=ANY(SELECT games FROM server_table WHERE server_id={guild_id});")
    teams = database.fetchall()
    r = []
    for t, in teams:
        r.append(t)
    return r

def team_name(team_id):
    database.execute(f"SELECT team_name FROM team_table WHERE team_id={team_id};")
    return database.fetchone()[0]

def team_elo(team_id):
    database.execute(f"SELECT team_elo FROM team_table WHERE team_id={team_id};")
    return json.loads(database.fetchone()[0])

def team_game(team_id):
    database.execute(f"SELECT game FROM team_table WHERE team_id={team_id};")
    return database.fetchone()[0]

def primary_players(team_id):
    database.execute(f"SELECT primary_players FROM team_table WHERE team_id={team_id};")
    return database.fetchone()[0]

def substitute_players(team_id):
    database.execute(f"SELECT sub_players FROM team_table WHERE team_id={team_id};")
    return database.fetchone()[0]
