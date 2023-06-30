class Config:

    def __init__(self, path="/config.json"):
        self._data = read_json(path)

    def get(self, property, default=None):
        if type(property) is str:
            return self._data.get(property, default)
        elif type(property) is tuple:
            parent = self._data
            for i in range(len(property)-1):
                parent = parent.get(property[i], None)
                if parent is None:
                    return default
            return parent.get(property[-1], default)
        else:
            return default

    def gpio(self, property, default=None):
        return getattr(board, self.get(property, default), None)

    def deinit(self):
        del self._data
