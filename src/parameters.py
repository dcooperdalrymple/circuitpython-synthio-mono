
class Parameter:
    def __init__(self, name="", label="", group="", range=None, value=0.0, set_callback=None, set_argument=None, object=None, property=None, mod=True, patch=True):
        self.name = name
        self.label = label
        self.group = group
        self.range = range
        self.set_callback = set_callback
        self.set_argument = set_argument
        self.object = object
        self.property = property
        self.mod = mod
        self.patch = patch
        self.set(value)
    def set(self, value):
        if type(value) is str:
            if type(self.range) is dict:
                value = unmap_dict(value, self.range)
            elif type(self.range) is list:
                value = unmap_array(value, self.range)
            else:
                return False
        value = min(max(value, 0.0), 1.0)
        if hasattr(self, "raw_value") and value == self.raw_value:
            return False
        self.raw_value = value
        if type(self.range) is dict:
            value = map_dict(value, self.range)
        elif type(self.range) is list:
            value = map_array(value, self.range, True)
        elif type(self.range) is tuple:
            if len(self.range) == 4: # Centered with threshold
                value = map_value_centered(value, self.range[0], self.range[1], self.range[2], self.range[3])
            elif len(self.range) == 3: # Centered
                value = map_value_centered(value, self.range[0], self.range[1], self.range[2])
            elif len(self.range) == 2: # Linear range
                value = map_value(value, self.range[0], self.range[1])
        elif type(self.range) is int or type(self.range) is float: # +/- linear range
            value = map_value(value, -self.range, self.range)
        elif type(self.range) is bool:
            value = map_boolean(value)
        self.format_value = value
        if self.set_callback:
            if self.set_argument:
                self.set_callback(value, self.set_argument)
            else:
                self.set_callback(value)
        elif self.object and self.property:
            if type(self.object) is dict:
                self.object[self.property] = value
            elif hasattr(self.object, self.property):
                setattr(self.object, self.property, value)
        return True
    def get(self):
        return self.raw_value
    def get_formatted_value(self, translate=True):
        if translate:
            value = None
            if type(self.range) is dict:
                value = list(self.range)[self.format_value]
            elif type(self.range) is list:
                value = self.range[self.format_value]
            if value:
                if type(value) is str:
                    return value
                elif type(value) is dict:
                    if value.get("label", None):
                        return value.get("label")
                    elif value.get("name", None):
                        return value.get("name")
                elif hasattr(value, "label"):
                    return value.label
                elif hasattr(value, "name"):
                    return value.name
        return self.format_value
    def get_steps(self):
        if type(self.range) is dict or type(self.range) is list:
            return len(self.range)-1
        elif type(self.range) is bool:
            return 1
        elif type(self.range) is tuple and len(self.range) == 2 and type(self.range[0]) is int:
            return self.range[1] - self.range[0] + 1
        elif type(self.range) is int: # +/- linear range
            return self.range * 2 + 1
        else:
            return 20
    def get_step_size(self):
        return 1.0/self.get_steps()
    def increment(self):
        return self.set(self.raw_value + self.get_step_size())
    def decrement(self):
        return self.set(self.raw_value - self.get_step_size())

class ParameterGroup:
    def __init__(self, name="", label=""):
        self.name = name
        self.label = label
        self.items = []
    def append(self, item):
        self.items.append(item)

class Parameters:
    def __init__(self):
        self._mod_parameter = 0
        self._mod_parameters = []
        self._items = []
        self._groups = []

    def add_group(self, item):
        self._groups.append(item)
    def add_groups(self, items):
        for item in items:
            self.add_group(item)

    def get_groups(self):
        return self._groups
    def get_group_count(self):
        return len(self._groups)
    def get_group(self, value):
        if type(value) is str:
            for group in self._groups:
                if group.name == value:
                    return group
        elif type(value) is int and abs(value) < self.get_group_count():
            return self._groups[value]
        return None

    def add_parameter(self, item):
        self._items.append(item)
        if item.mod:
            self._mod_parameters.append(item.name)
        group = self.get_group(item.group)
        if group:
            group.append(item)
    def add_parameters(self, items):
        for item in items:
            self.add_parameter(item)

    def get_parameters(self):
        return self._items
    def get_parameter_count(self, group=None):
        if type(group) is str or type(group) is int:
            _group = self.get_group(group)
            if _group:
                return len(_group.items)
            return 0
        else:
            return len(self._items)
    def get_parameter(self, value):
        if type(value) is str:
            for parameter in self._items:
                if parameter.name == value:
                    return parameter
        elif type(value) is int and abs(value) < self.get_parameter_count():
            return self._items[value]
        return None

    def get_mod_parameters(self):
        return self._mod_parameters
    def get_mod_parameter(self):
        if not self._mod_parameters:
            return "volume"
        return self._mod_parameters[self._mod_parameter]
    def set_mod_parameter(self, value):
        self._mod_parameter = value
