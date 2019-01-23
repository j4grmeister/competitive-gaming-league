class Cache:
    def __init__(self):
        self.data = {}

    def add(self, category, key, value):
        if category not in self.data:
            self.data[category] = {}
        self.data[category][key] = value

    def get(self, category, key):
        if category not in self.data:
            return None
        if key not in self.data[category]:
            return None
        return self.data[category][key]

    def pop(self, categoy, key):
        if category not in self.data:
            return None
        if key not in self.data[category]:
            return None
        v = self.data[category][key]
        del self.data[category][key]
        return v

    def delete(self, category, key):
        if category not in self.data:
            return
        if key not in self.data[category]:
            return
        del self.data[category][key]
