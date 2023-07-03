class MenuItem:
    def __init__(self, group_index=0, group=None, parameter_index=0, parameter=None):
        self.group_index = group_index
        self.group = group
        self.parameter_index = parameter_index
        self.parameter = parameter

class Menu:
    def __init__(self, parameters, display, patches):
        self._parameters = parameters
        self._display = display
        self._patches = patches
        self._item = None
        self._selected = False
        self._saving = False
        self._saving_index = 0 # 0 is index, 1+ is name
        self._save_name = [" " for i in range(16)]
        self._save_index = 0
        self._characters = " abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!-_#$%&+@~^"

    def _get_item_by_index(self, group_index, parameter_index):
        group_index = group_index % self._parameters.get_group_count()
        group = self._parameters.get_group(group_index)
        parameter_index = parameter_index % len(group.items)
        parameter = group.items[parameter_index]
        return MenuItem(group_index, group, parameter_index, parameter)
    def _get_item_by_name(self, name):
        parameter = self._parameters.get_parameter(name)
        group = self._parameters.get_group(parameter.group)
        return MenuItem(self._get_group_index(group), group, self._get_parameter_index(group, parameter), parameter)
    def _get_group_index(self, group):
        groups = self._parameters.get_groups()
        for i in range(len(groups)):
            if groups[i] == group:
                return i
        return 0
    def _get_parameter_index(self, group, parameter):
        for i in range(len(group.items)):
            if group.items[i] == parameter:
                return i
        return 0

    def _queue(self):
        if self._saving:
            self._display.queue("Save Patch", "{:02d}".format(self._save_index), "".join(self._save_name))
            self._display.set_save_index(self._saving_index)
        else:
            if not self._item:
                return False
            self._display.queue(self._item.parameter.label, self._item.group.label, self._item.parameter.get_formatted_value())
        return True
    def _queue_by_index(self, group_index, parameter_index):
        item = self._get_item_by_index(group_index, parameter_index)
        if not item:
            return False
        self._item = item
        return self._queue()
    def display(self, name=None):
        if not name:
            return self._queue()
        if not self._item or self._item.parameter.name != name:
            self._item = self._get_item_by_name(name)
        return self._queue()

    def first(self):
        return self._queue_by_index(0, 0)
    def last(self):
        return self._queue_by_index(-1, -1)
    def next(self):
        if not self._item:
            return self.first()
        if self._item.parameter_index >= len(self._item.group.items)-1:
            return self._queue_by_index(self._item.group_index+1, 0)
        else:
            return self._queue_by_index(self._item.group_index, self._item.parameter_index+1)
    def previous(self):
        if not self._item:
            return self.last()
        if self._item.parameter_index <= 0:
            return self._queue_by_index(self._item.group_index-1, -1)
        else:
            return self._queue_by_index(self._item.group_index, self._item.parameter_index-1)

    def increment(self):
        if self._saving:
            if self._saving_index == 0:
                self._save_index = (self._save_index + 1) % 100
                return self._queue()
            elif self._saving_index - 1 < len(self._save_name):
                i = self._characters.index(self._save_name[self._saving_index-1])
                self._save_name[self._saving_index-1] = self._characters[(i+1)%len(self._characters)]
                return self._queue()
        elif self._selected and self._item:
            if self._item.parameter.increment():
                return self._queue()
            else:
                return False
        else:
            return self.next()
    def decrement(self):
        if self._saving:
            if self._saving_index == 0:
                self._save_index = (self._save_index - 1) % 100
                return self._queue()
            elif self._saving_index - 1 < len(self._save_name):
                i = self._characters.index(self._save_name[self._saving_index-1])
                self._save_name[self._saving_index-1] = self._characters[i-1]
                return self._queue()
        elif self._selected and self._item:
            if self._item.parameter.decrement():
                return self._queue()
            else:
                return False
        else:
            return self.previous()

    def toggle_select(self):
        if self._saving:
            self._saving_index = (self._saving_index + 1) % 17 # max string length is 16
            return self._queue()
        elif self._selected:
            self.deselect()
        else:
            self.select()
    def select(self):
        self._selected = True
        self._display.set_selected(self._selected)
    def deselect(self):
        self._selected = False
        self._display.set_selected(self._selected)
    def selected(self):
        return self._selected

    def toggle_save(self):
        if not self._saving:
            parameter = self._parameters.get_parameter("patch")
            self._save_index = parameter.get_formatted_value(False)
            self._save_name = [i for i in truncate_str(self._patches.get_name(self._save_index), 16)]
            self._saving = True
            self._saving_index = 0
        else:
            self._saving = False
        self._queue()
        self._display.set_selected(self._saving)
    def confirm_save(self):
        if not self._saving or not "".join(self._save_name).strip():
            return
        self._save_index = self._save_index % 100
        self._patches.save(self._save_index, "".join(self._save_name))
        self._saving = False
        self._queue()
        self._display.set_selected(self._saving)

    def deinit(self):
        del self._parameters
        del self._display
        del self._item
        del self._save_name
        del self._characters
