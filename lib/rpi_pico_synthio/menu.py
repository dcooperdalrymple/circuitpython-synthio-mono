"""
rpi-pico-synthio
2023 Cooper Dalrymple - me@dcdalrymple.com
GPL v3 License

File: menu.py
Title: Menu Display
Version: 0.1.0
Since: 0.1.0
"""

import json

import displayio
import adafruit_displayio_ssd1306
import terminalio
from adafruit_display_text import label

from busio import I2C
from digitalio import DigitalInOut, Direction, Pull
from rotaryio import IncrementalEncoder
from adafruit_debouncer import Debouncer

SPLASH_PATH = "/splash.bmp"
MENU_CONFIG = "menu.json"

class Menu:

    def __init__(self, scl, sda, encoder_pin_a, encoder_pin_b, button_pin, address=0x3c, width=128, height=64):
        displayio.release_displays()

        self.i2c = I2C(scl=scl, sda=sda)
        self.display_bus = displayio.I2CDisplay(self.i2c, device_address=address)
        self.display = adafruit_displayio_ssd1306.SSD1306(self.display_bus, width=width, height=height)

        self.buffer = displayio.Group()
        self.display.show(self.buffer)

        self.encoder = IncrementalEncoder(
            pin_a=encoder_pin_a,
            pin_b=encoder_pin_b
        )
        self.last_position = self.encoder.position

        self.button_pin = DigitalInOut(button_pin)
        self.button_pin.direction = Direction.INPUT
        self.button_pin.pull = Pull.UP
        self.button = Debouncer(self.button_pin)

        self.callbacks = []

    def clear(self):
        if hasattr(self, "splash_text"):
            del self.splash_text
        for i in reversed(range(len(self.buffer))):
            del self.buffer[i]

    def splash_image(self):
        self.clear()

        # Only compatible with CircuitPython 7
        bitmap = displayio.OnDiskBitmap(SPLASH_PATH)
        tile_grid = displayio.TileGrid(
            bitmap,
            pixel_shader=bitmap.pixel_shader
        )
        self.buffer.append(tile_grid)

        return True

    def splash_message(self, text):
        if not hasattr(self, "splash_text"):
            self.splash_text = label.Label(terminalio.FONT, text="", color=0xFFFFFF, x=0, y=3)
            self.splash_text.anchor_point = (0, 0.5)
            self.buffer.append(self.splash_text)

        self.splash_text.text = text
        return True

    def _create_group(self, data, callback=None, parent=None):
        if not "key" in data or not "name" in data or not "type" in data:
            return None

        group_class = None
        if data["type"] == "group":
            if not "items" in data:
                return None
            group_class = MenuGroup
        elif data["type"] == "envelope":
            group_class = MenuGroupEnvelope
        elif data["type"] == "lfo":
            group_class = MenuGroupLfo
        if group_class is None:
            return None

        group = group_class(data["key"], data["name"], parent)
        if parent != None:
            group.append(MenuReturn(parent))

        if data["type"] == "group":
            for item_data in data["items"]:
                if not "key" in item_data or not "name" in item_data or not "type" in item_data:
                    continue

                item = None
                if item_data["type"] == "group" or item_data["type"] == "envelope" or item_data["type"] == "lfo":
                    item = self._create_group(item_data, callback, group)
                elif item_data["type"] == "string":
                    item = MenuValueString(item_data["key"], item_data["name"], item_data["value"])
                elif item_data["type"] == "bool":
                    item = MenuValueBool(item_data["key"], item_data["name"], item_data["value"])
                    if callback != None:
                        item.set_callback(callback)
                elif item_data["type"] == "number":
                    item = MenuValueNumber(item_data["key"], item_data["name"], item_data["value"])
                    if "min" in item_data:
                        item.set_min(item_data["min"])
                    if "max" in item_data:
                        item.set_max(item_data["max"])
                    if "step" in item_data:
                        item.set_step(item_data["step"])
                    if "precision" in item_data:
                        item.set_precision(item_data["precision"])
                    if callback != None:
                        item.set_callback(callback)
                elif item_data["type"] == "selector":
                    item = MenuValueSelector(item_data["key"], item_data["name"], item_data["items"])
                    if "value" in item_data:
                        item.set_value(item_data["value"])
                    if callback != None:
                        item.set_callback(callback)

                if item != None:
                    group.append(item)
        else:
            group.append_items(callback)

        return group

    def setup(self):
        self.clear()

        # Setup data
        file = open(MENU_CONFIG, "r")
        data = json.loads(file.read())
        self.group = self._create_group(data, self.handleMenuItem)
        self.current_group = self.group
        self.current_item = None

        # Setup items
        self.draw_items = displayio.Group()
        for i in range(3):
            draw_item = displayio.Group()

            color_bitmap = displayio.Bitmap(self.display.width, int(self.display.height/3+1), 1)
            color_palette = displayio.Palette(1)
            color_palette[0] = 0xFFFFFF

            bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=int(self.display.height/3*i))
            draw_item.append(bg_sprite)

            inner_bitmap = displayio.Bitmap(self.display.width-2, int(self.display.height/3-1), 1)
            inner_palette = displayio.Palette(1)
            inner_palette[0] = 0x000000
            inner_sprite = displayio.TileGrid(inner_bitmap, pixel_shader=inner_palette, x=1, y=int(self.display.height/3*i+1))
            draw_item.append(inner_sprite)

            name_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF)
            name_label.anchor_point = (0, 0.5)
            name_label.anchored_position = (3, int(self.display.height/6*(i*2+1)))
            draw_item.append(name_label)

            value_label = label.Label(terminalio.FONT, text="", color=0xFFFFFF)
            value_label.anchor_point = (1.0, 0.5)
            value_label.anchored_position = (self.display.width-3, int(self.display.height/6*(i*2+1)))
            draw_item.append(value_label)

            draw_item.x = -self.display.width
            self.draw_items.append(draw_item)
        self.buffer.append(self.draw_items)

        # Draw frame
        self.draw()

    def addItemEvent(self, callback):
        self.callbacks.append(callback)

    def handleMenuItem(self, item):
        if self.callbacks:
            for callback in self.callbacks:
                callback(item)

    def update(self):
        redraw = False

        position = self.encoder.position
        if position != self.last_position and hasattr(self, "current_group"): # Encoder turn
            redraw = True
            if position > self.last_position:
                for i in range(position - self.last_position):
                    if hasattr(self, "current_item") and self.current_item != None:
                        self.current_item.increment()
                    else:
                        self.current_group.next()
            else:
                for i in range(self.last_position - position):
                    if hasattr(self, "current_item") and self.current_item != None:
                        self.current_item.decrement()
                    else:
                        self.current_group.previous()
        self.last_position = position

        self.button.update()
        # Press: self.button.fell
        if self.button.rose and hasattr(self, "current_group"): # Release
            if self.current_item != None:
                self.current_item = None
                redraw = True
            else:
                item = self.current_group.get_selected()
                if item.get_type() == "group":
                    self.current_group = item
                    self.current_item = None
                    redraw = True
                elif item.get_type() == "return":
                    if item.get_parent() != None:
                        self.current_group = item.get_parent()
                        self.current_item = None
                        redraw = True
                elif item.get_type() != "string":
                    self.current_item = item
                    redraw = True

        if redraw:
            self.draw()

    def draw(self):
        if not hasattr(self, "current_group") or not hasattr(self, "draw_items"):
            return

        index = self.current_group.get_selected_index()

        if index > 0:
            self.draw_item(0, self.current_group[index - 1])
        else:
            self.draw_item(0, False)

        if hasattr(self, "current_item") and self.current_item != None:
            self.draw_item(1, self.current_group[index], True)
        else:
            self.draw_item(1, self.current_group[index], False)

        if index < len(self.current_group) - 1:
            self.draw_item(2, self.current_group[index + 1])
        else:
            self.draw_item(2, False)

    def draw_item(self, index, item=False, selected=False):
        if index < 0 or index >= len(self.draw_items):
            return False

        if selected:
            self.draw_items[index][1].pixel_shader[0] = 0xFFFFFF
            self.draw_items[index][2].color = 0x000000
            self.draw_items[index][3].color = 0x000000
        else:
            self.draw_items[index][1].pixel_shader[0] = 0x000000
            self.draw_items[index][2].color = 0xFFFFFF
            self.draw_items[index][3].color = 0xFFFFFF

        if item == False:
            self._draw_item(index, False)
        elif item.get_type() == "group":
            self._draw_item(index, True, item.get_name(), ">")
        elif item.get_type() == "return":
            self._draw_item(index, True, item.get_name(), "<")
        elif item.get_type() == "selector":
            self._draw_item(index, True, item.get_name(), str(item.get_value()))
        elif item.get_type() == "envelope":
            self._draw_item(index, True, item.get_name(), item.get_values())
        elif not hasattr(item, "get") or item.get() == None:
            self._draw_item(index, True, item.get_name())
        else:
            self._draw_item(index, True, item.get_name(), str(item.get()))

    def _draw_item(self, index, visible=True, name="", value=""):
        if index < 0 or index >= len(self.draw_items):
            return False

        if visible:
            self.draw_items[index].x = 0
        else:
            self.draw_items[index].x = -self.display.width

        self.draw_items[index][2].text = name
        self.draw_items[index][3].text = value

        return True

    def find_item(self, key, group=None):
        if group == None:
            group = self.group
        if group.get_key() == key:
            return group
        for item in group:
            if item.get_type() == "group":
                found = self.find_item(key, item)
                if found != None:
                    return found
            elif item.get_key() == key:
                return item
        return None

    def deinit(self):
        self.encoder.deinit()

class MenuItem:
    def __init__(self, type="", key="", name=""):
        self._type = type
        self._key = key
        self._name = name
    def get_type(self):
        return self._type
    def get_key(self):
        return self._key
    def get_name(self):
        return self._name

class MenuGroup(MenuItem):
    def __init__(self, key="", name="", parent=None):
        super().__init__("group", key, name)
        self._parent = parent

        self._items = list()
        self._selected = 0
        self._index = 0

    # Properties
    def get_parent(self):
        return self._parent
    def get_selected_index(self):
        return self._selected
    def get_selected(self):
        return self[self._selected]

    # Methods
    def next(self):
        if self._selected < len(self._items) - 1:
            self._selected += 1
            return True
        return False
    def previous(self):
        if self._selected > 0:
            self._selected -= 1
            return True
        return False

    # Iteration
    def __iter__(self):
        return self
    def __next__(self):
        if self._index < len(self._items):
            result = self._items[self._index]
            self._index += 1
            return result
        raise StopIteration
    def __len__(self):
        return len(self._items)
    def __bool__(self):
        if len(self._items) > 0:
            return True
        return False
    def __getitem__(self, index):
        if index >= 0 and index < len(self._items):
            return self._items[index]
        return None
    def __setitem__(self, index, value):
        if index >= 0 and index < len(self._items):
            self._items[index] = value
    def __delitem__(self, index):
        if index >= 0 and index < len(self._items):
            del self._items[index]
    def append(self, item):
        self._items.append(item)
    def insert(self, index, item):
        self._items.insert(index, item)
    def index(self, item):
        return self._items.index(item)
    def pop(self, i=-1):
        return self._items.pop(i)
    def remove(self, item):
        self._items.remove(item)

class MenuReturn(MenuItem):
    def __init__(self, parent):
        super().__init__("return", "return_"+parent.get_key(), "Return")
        self._parent = parent
    def get_parent(self):
        return self._parent

class MenuValue(MenuItem):
    def __init__(self, type="", key="", name="", callback=None):
        super().__init__(type, key, name)
        self._value = None
        self._callback = callback
    def get_key(self):
        return self._key
    def get_name(self):
        return self._name
    def get(self):
        return self._value
    def set(self, value):
        self._value = value
        self._do_callback()
        return True
    def _do_callback(self):
        if self._callback != None:
            self._callback(self)
    def set_callback(self, cb):
        self._callback = cb
    def clear_callback(self):
        self._callback = None
    def increment(self):
        pass
    def decrement(self):
        pass

class MenuValueString(MenuValue):
    def __init__(self, key="", name="", text="", callback=None):
        super().__init__("string", key, name, callback)
        self.set(text)

class MenuValueBool(MenuValue):
    def __init__(self, key="", name="", value=False, callback=None):
        super().__init__("bool", key, name, callback)
        self.set(value)
    def set(self, value):
        if type(value) != type(False):
            return False
        if self._value == value:
            return False
        self._value = value
        return True
    def increment(self):
        return self.set(True)
    def decrement(self):
        return self.set(False)

class MenuValueNumber(MenuValue):
    def __init__(self, key="", name="", value=0, min=None, max=None, step=1, precision=0, callback=None):
        super().__init__("number", key, name, callback)
        self._value = value
        self._min = min
        self._max = max
        self._step = step
        self._precision = precision
    def set(self, value):
        if self._min != None:
            value = max(value, self._min)
        if self._max != None:
            value = min(value, self._max)
        if value == self._value:
            return False
        self._value = round(value, self._precision)
        self._do_callback()
        return True
    def increment(self):
        return self.set(self._value + self._step)
    def decrement(self):
        return self.set(self._value - self._step)
    def set_min(self, value):
        self._min = value
    def set_max(self, value):
        self._max = value
    def set_step(self, value):
        self._step = value
    def set_precision(self, value):
        self._precision = int(value)

class MenuValueSelector(MenuValueNumber):
    def __init__(self, key="", name="", items=list(), callback=None):
        super().__init__(key, name, callback)
        self._type = "selector"
        self._items = items
        self._value = 0
        self.set_min(0)
        self.set_max(len(self._items) - 1)
    def get_value(self):
        if self._value >= 0 and self._value < len(self._items):
            return self._items[self._value]
        return None
    def set_value(self, value):
        try:
            self._value = self._items.index(value)
            self._do_callback()
            return True
        except:
            return False
    def get_items(self):
        return self._items
    def set_items(self, items):
        self._items = items
        self.set_max(len(items) - 1)
    def increment(self):
        return self.set(self._value + 1)
    def decrement(self):
        return self.set(self._value - 1)

class MenuGroupEnvelope(MenuGroup):
    def __init__(self, key="", name="", parent=None):
        super().__init__(key, name, parent)
    def append_items(self, callback=None):
        self.append(MenuValueNumber(
            key=self._key+"_attack_time",
            name="Attack Time",
            value=0.0,
            min=0.0,
            max=1.0,
            step=0.05,
            precision=2,
            callback=callback
        ))
        self.append(MenuValueNumber(
            key=self._key+"_decay_time",
            name="Decay Time",
            value=0.05,
            min=0.0,
            max=1.0,
            step=0.05,
            precision=2,
            callback=callback
        ))
        self.append(MenuValueNumber(
            key=self._key+"_release_time",
            name="Release Time",
            value=0,
            min=0.0,
            max=1.0,
            step=0.05,
            precision=2,
            callback=callback
        ))
        self.append(MenuValueNumber(
            key=self._key+"_attack_level",
            name="Attack Level",
            value=1.0,
            min=0.0,
            max=1.0,
            step=0.05,
            precision=2,
            callback=callback
        ))
        self.append(MenuValueNumber(
            key=self._key+"_sustain_level",
            name="Sustain Level",
            value=0.75,
            min=0.0,
            max=1.0,
            step=0.05,
            precision=2,
            callback=callback
        ))

class MenuGroupLfo(MenuGroup):
    def __init__(self, key="",  name="", parent=None):
        super().__init__(key, name, parent)
    def append_items(self, callback=None):
        self.append(MenuValueNumber(
            key=self._key+"_rate",
            name="Rate",
            value=1.0,
            min=0.0,
            max=1.0,
            step=0.05,
            precision=2,
            callback=callback
        ))
        self.append(MenuValueNumber(
            key=self._key+"_depth",
            name="Depth",
            value=0.0,
            min=0.0,
            max=1.0,
            step=0.05,
            precision=2,
            callback=callback
        ))
        self.append(MenuValueNumber(
            key=self._key+"_level",
            name="Level",
            value=0.0,
            min=0.0,
            max=1.0,
            step=0.05,
            precision=2,
            callback=callback
        ))
