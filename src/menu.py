
class MenuItem:
    def __init__(self, group_index=0, group=None, parameter_index=0, parameter=None):
        self.group_index = group_index
        self.group = group
        self.parameter_index = parameter_index
        self.parameter = parameter

class Menu:
    def __init__(self, parameters, display):
        self._parameters = parameters
        self._display = display
        self._item = None
        self._selected = False
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
        if self._selected and self._item:
            if self._item.parameter.increment():
                return self._queue()
            else:
                return False
        else:
            return self.next()
    def decrement(self):
        if self._selected and self._item:
            if self._item.parameter.decrement():
                return self._queue()
            else:
                return False
        else:
            return self.previous()
    def toggle(self):
        if self._selected:
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
