class Display:
    def __init__(self, update=0.2):
        self._update = update
        self._now = 0
        self._queued = None
    def set_title(self, text):
        pass
    def set_group(self, text):
        pass
    def set_value(self, text):
        pass
    def set_selected(self, value):
        pass
    def queue(self, title, group, value):
        self._queued = (title, group, value)
    def update(self):
        now = time.monotonic()
        if now < self._now + self._update:
            return
        self._now = now

        if self._queued:
            self.set_title(self._queued[0])
            self.set_group(self._queued[1])
            self.set_value(self._queued[2])
            self._queued = None
    def deinit(self):
        pass

class DisplaySSD1306(Display):
    def __init__(self, scl, sda, speed, address, width, height, update=0.2):
        from busio import I2C
        import displayio, adafruit_displayio_ssd1306, terminalio
        from adafruit_display_text import label

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
    def deinit(self):
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
    else:
        return Display() # Dummy display
