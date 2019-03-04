import os
import psycopg2

DATABASE_URL = os.environ['DATABASE_URL']
conn = psycopg2.connect(DATABASE_URL, sslmode='require')
cur = conn.cursor()

def execute(sql):
    cur.execute(sql)
def commit():
    conn.commit()
def fetchone():
    return cur.fetchone()
def fetchall():
    return cur.fetchall()

#only use if entry is known to exist
def server_setting(serverid, setting):
    execute(f"""
        SELECT {setting}
        FROM servers
        WHERE server_id='{serverid}'
    ;""")
    return fetchone()[0]
def player_setting(discordid, setting):
    execute(f"""
        SELECT {setting}
        FROM players
        WHERE discord_id='{discordid}'
    ;""")
    return fetchone()[0]
