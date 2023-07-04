class Patches:
    def __init__(self, parameters, dir="/patches"):
        self._parameters = parameters
        self._dir = dir
        self._items = {}
        for filename in self._list_filenames():
            self._items[self._get_filename_index(filename)] = filename

    def _valid_filename(self, filename):
        return len(filename) > len("00-a.json") and filename[-5:] == ".json" and filename[0:2].isdigit() and filename[2] == "-"
    def _get_filename_index(self, filename):
        if not self._valid_filename(filename):
            return 0
        return int(filename[0:2])
    def _list_filenames(self):
        try:
            return [filename for filename in os.listdir(self._dir) if self._valid_filename(filename)]
        except:
            return []

    def get_filename(self, index):
        if type(index) is str and index.isdigit():
            index = int(index)
        if not type(index) is int or index > 99 or not self._items or not index in self._items:
            return None
        return self._items[index]
    def get_path(self, index):
        filename = self.get_filename(index)
        if not filename:
            return None
        return self._dir + "/" + filename
    def get_name(self, index):
        filename = self.get_filename(index)
        if not filename:
            return ""
        return filename[3:-5]
    def get_list(self):
        return self._items

    def remove(self, index):
        path = self.get_path(index)
        if not path:
            return False
        try:
            os.remove(path)
            return True
        except:
            return False
    def read(self, index):
        path = self.get_path(index)
        if not path:
            return False
        data = read_json(path)
        if not data or not "parameters" in data:
            print("Invalid Data")
            return False
        for name in data["parameters"]:
            parameter = self._parameters.get_parameter(name)
            if parameter:
                parameter.set(data["parameters"][name])
        return True
    def save(self, index=0, name="Patch"):
        index = index % 100
        name = name.strip()
        data = {
            "index": 0,
            "name": name,
            "parameters": {},
        }
        for parameter in self._parameters.get_parameters():
            if parameter.patch:
                data["parameters"][parameter.name] = parameter.get_formatted_value(True)
        self.remove(index)
        filename = "{:02d}-{}.json".format(index, name)
        path = self._dir + "/" + filename
        if not save_json(path, data):
            return False
        self._items[index] = filename
        parameter = self._parameters.get_parameter("patch")
        parameter.range = self.get_list()
        parameter.set(index)
        return True
    def read_first(self):
        return self.read(0)

    def deinit(self):
        del self._parameters
        del self._items
