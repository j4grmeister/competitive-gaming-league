def escape_sql(query):
    escaped = query
    escaped.replace("'", "''")
    return escaped
