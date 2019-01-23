data = {}

def add(category, key, value):
    if category not in data:
        data[category] = {}
    data[category][key] = value

def get(category, key):
    if category not in data:
        return None
    if key not in data[category]:
        return None
    return data[category][key]

def pop(categoy, key):
    if category not in data:
        return None
    if key not in data[category]:
        return None
    v = data[category][key]
    del sdata[category][key]
    return v

def delete(category, key):
    if category not in data:
        return
    if key not in data[category]:
        return
    del data[category][key]
