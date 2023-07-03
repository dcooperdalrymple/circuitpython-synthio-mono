class Display:
    def __init__(self, update=0.2):
        self._delay = update
        self._now = 0
        self._queued = None
        self._cursor = False
        self._cursor_pos = (0,0)
        self._cursor_visible = False
    def set_title(self, text):
        pass
    def set_group(self, text):
        pass
    def set_value(self, text):
        pass
    def set_selected(self, value):
        pass
    def show_cursor(self, column=0, row=0):
        self._cursor = True
        self._cursor_pos = (column, row)
    def hide_cursor(self):
        self._cursor = False
    def queue(self, title, group, value):
        self._queued = (title, group, value)
    def update(self, now=None):
        if not now:
            now = time.monotonic()
        if now < self._now + self._delay:
            return
        self._now = now
        self._update()
    def _update(self):
        if self._cursor:
            self._cursor_visible = not self._cursor_visible
        self._update_cursor()
        if self._queued:
            self.set_title(self._queued[0])
            self.set_group(self._queued[1])
            self.set_value(self._queued[2])
            self._queued = None
    def _update_cursor(self):
        pass
    def deinit(self):
        del self._queued
        pass

class DisplaySSD1306(Display):
    def __init__(self, scl, sda, speed, address, width, height, update=0.2):
        from busio import I2C
        import displayio, adafruit_displayio_ssd1306, terminalio
        from adafruit_display_text import label
        from adafruit_display_shapes.rect import Rect

        # Release REPL
        displayio.release_displays()

        self._width = width
        self._height = height

        self._i2c = I2C(
            scl=scl,
            sda=sda,
            frequency=speed
        )
        self._bus = displayio.I2CDisplay(
            self._i2c,
            device_address=address
        )
        self._driver = adafruit_displayio_ssd1306.SSD1306(
            self._bus,
            width=self._width,
            height=self._height
        )

        self._group = displayio.Group()
        self._driver.show(self._group)

        self._bg_bitmap = displayio.Bitmap(self._width, self._height, 1)
        self._bg_palette = displayio.Palette(1)
        self._bg_palette[0] = 0x000000
        self._bg_sprite = displayio.TileGrid(
            self._bg_bitmap,
            pixel_shader=self._bg_palette,
            x=0,
            y=0
        )
        self._group.append(self._bg_sprite)

        self._title_label = label.Label(
            terminalio.FONT,
            text="",
            color=0xFFFFFF,
            background_color=None
        )
        self._group.append(self._title_label)

        self._group_label = label.Label(
            terminalio.FONT,
            text="",
            color=0x000000,
            background_color=0xFFFFFF
        )
        self._group.append(self._group_label)

        self._value_label = label.Label(
            terminalio.FONT,
            text="",
            color=0xFFFFFF,
            background_color=None
        )
        self._group.append(self._value_label)

        self._cursor = Rect(
            x=0,
            y=0,
            width=8,
            height=2,
            fill=None
        )
        self._group.append(self._cursor)

        super().__init__(update)
    def set_title(self, text):
        self._title_label.text = str(text)
    def set_group(self, text):
        self._group_label.text = str(text)
    def set_value(self, text):
        if type(text) == type(0.5):
            text = "{:.2f}".format(text)
        self._value_label.text = str(text)
    def set_selected(self, value):
        if value:
            self._title_label.color = 0x000000
            self._title_label.background_color = 0xFFFFFF
        else:
            self._title_label.color = 0xFFFFFF
            self._title_label.background_color = 0x000000
    def _update_cursor(self):
        if not self._cursor:
            return
        if self._cursor_visible:
            self._cursor.fill = 0xFFFFFF
            self._cursor.x = self._cursor_pos[0]*8
            self._cursor.y = (self._cursor_pos[1]+1)*8-self._cursor.height
        else:
            self._cursor.fill = None
    def deinit(self):
        from busio import I2C
        import displayio, adafruit_displayio_ssd1306, terminalio
        from adafruit_display_text import label

        displayio.release_displays()

        super().deinit()

class DisplaySSD1306_128x32(DisplaySSD1306):
    def __init__(self, scl, sda, speed, address, update=0.2):
        super().__init__(scl, sda, speed, address, 128, 32, update)
        self._title_label.anchor_point = (0.0,0.5)
        self._title_label.anchored_position = (0,self._height//4)
        self._group_label.anchor_point = (1.0,0.5)
        self._group_label.anchored_position = (self._width,self._height//4)
        self._value_label.anchor_point = (0.0,0.5)
        self._value_label.anchored_position = (0,self._height//4*3)

class DisplaySSD1306_128x64(DisplaySSD1306):
    def __init__(self, scl, sda, speed, address, update=0.2):
        super().__init__(scl, sda, speed, address, 128, 64, update)
        self._group_label.anchor_point = (0.5,0.5)
        self._group_label.anchored_position = (self._width//2,self._height//8)
        self._title_label.anchor_point = (0.5,0.5)
        self._title_label.anchored_position = (self._width//2,self._height//8*3)
        self._value_label.anchor_point = (0.5,0.5)
        self._value_label.anchored_position = (self._width//2,self.height//4*3)

class DisplayCharacterLCD(Display):
    def __init__(self, rs, en, d7, d6, d5, d4, columns, rows, update=0.2):
        from digitalio import DigitalInOut
        from adafruit_character_lcd.character_lcd import Character_LCD_Mono
        import adafruit_mcp230xx, adafruit_74hc595, adafruit_bus_device

        self._rs = DigitalInOut(rs)
        self._en = DigitalInOut(en)
        self._d7 = DigitalInOut(d7)
        self._d6 = DigitalInOut(d6)
        self._d5 = DigitalInOut(d5)
        self._d4 = DigitalInOut(d4)
        self._columns = columns
        self._rows = rows

        self._lcd = Character_LCD_Mono(self._rs, self._en, self._d4, self._d5, self._d6, self._d7, self._columns, self._rows)
        self._lcd.cursor = False
        self._lcd.backlight = True
        self._lcd.text_direction = lcd.LEFT_TO_RIGHT

        self._select_pos = (0, self._columns-1)

        super().__init__(update)
    def set_selected(self, value):
        if value:
            self.cursor = True
            self.blink = True
        else:
            self.cursor = False
            self.blink = False
    def _write(self, value, length=None, right_aligned=False, column=0, row=0):
        if not length:
            length = self._columns
        if type(value) is float:
            value = "{:.2f}".format(value)
        lcd.cursor_position(column, row)
        lcd.message = truncate_str(str(value), length, right_aligned)
        lcd.cursor_position(self._select_pos[0], self._select_pos[1])
    def _update_cursor(self):
        if not self._cursor:
            return
        self._lcd.cursor_position(self._cursor_pos[0], self._cursor_pos[1])

    def deinit(self):
        del self._select_pos
        del self._lcd
        del self._rs
        del self._en
        del self._d7
        del self._d6
        del self._d5
        del self._d4

        super().deinit()

class DisplayCharacterLCD_1602(DisplayCharacterLCD):
    def __init__(self, rs, en, d7, d6, d5, d4, update=0.2):
        super().__init__(rs, en, d7, d6, d5, d4, 16, 2)
    def set_title(self, text):
        self._write(text, self._columns-6, False, 0, 0)
    def set_group(self, text):
        self._write(text, 6, True, self._columns-6, 0)
    def set_value(self, text):
        self._write(text, self._columns, True, 0, 1)

class DisplayCharacterLCD_1604(DisplayCharacterLCD):
    def __init__(self, rs, en, d7, d6, d5, d4, update=0.2):
        super().__init__(rs, en, d7, d6, d5, d4, 16, 4)
    def set_title(self, text):
        self._write(text, row=1)
    def set_group(self, text):
        self._write(text, row=0)
    def set_value(self, text):
        self._write(text, row=3)

def get_display(config):
    type = config.get(("display", "type"), "ssd1306_128x32")
    if type == "ssd1306_128x32":
        return DisplaySSD1306_128x32(
            scl=config.gpio(("display", "scl"), "GP21"),
            sda=config.gpio(("display", "sda"), "GP20"),
            speed=config.get(("display", "speed"), 1000000),
            address=config.get(("display", "address"), 0x3c)
        )
    elif type == "ssd1306_128x64":
        return DisplaySSD1306_128x64(
            scl=config.gpio(("display", "scl"), "GP21"),
            sda=config.gpio(("display", "sda"), "GP20"),
            speed=config.get(("display", "speed"), 1000000),
            address=config.get(("display", "address"), 0x3c)
        )
    elif type == "1602":
        return DisplayCharacterLCD_1602(
            rs=config.gpio(("display", "rs")),
            en=config.gpio(("display", "en")),
            d7=config.gpio(("display", "d7")),
            d6=config.gpio(("display", "d6")),
            d5=config.gpio(("display", "d5")),
            d4=config.gpio(("display", "d4"))
        )
    elif type == "1604":
        return DisplayCharacterLCD_1604(
            rs=config.gpio(("display", "rs")),
            en=config.gpio(("display", "en")),
            d7=config.gpio(("display", "d7")),
            d6=config.gpio(("display", "d6")),
            d5=config.gpio(("display", "d5")),
            d4=config.gpio(("display", "d4"))
        )
    else:
        return Display() # Dummy display
