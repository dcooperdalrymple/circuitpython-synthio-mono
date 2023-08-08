class Display:
    def __init__(self, update=0.2):
        self._delay = update
        self._now = 0
        self._queued = None
        self._cursor = False
        self._cursor_pos = (0,0)
        self._cursor_update = False
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
        self._cursor_update = True
    def hide_cursor(self):
        self._cursor = False
        self._cursor_update = True
    def set_save_index(self, i):
        pass
    def queue(self, title, group, value):
        self._queued = (title, group, value)
    def update(self, now=None):
        if self._delay > 0.0:
            if not now:
                now = time.monotonic()
            if now < self._now + self._delay:
                return
        self._now = now
        self._update()
    def _update(self):
        if self._cursor_update:
            self._cursor_update = False
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

class DisplayCharacterLCD(Display):
    def __init__(self, rs, en, d4, d5, d6, d7, columns, rows, vo=None, contrast=0.5):
        from pwmio import PWMOut
        from adafruit_character_lcd.character_lcd import Character_LCD_Mono
        import adafruit_mcp230xx, adafruit_74hc595, adafruit_bus_device

        self._rs = DigitalInOut(rs)
        self._en = DigitalInOut(en)
        self._d4 = DigitalInOut(d4)
        self._d5 = DigitalInOut(d5)
        self._d6 = DigitalInOut(d6)
        self._d7 = DigitalInOut(d7)
        self._columns = columns
        self._rows = rows
        self._vo = None
        if vo:
            self._vo = PWMOut(vo)
            self.set_contrast(contrast)

        self._lcd = Character_LCD_Mono(self._rs, self._en, self._d4, self._d5, self._d6, self._d7, self._columns, self._rows)
        self._lcd.cursor = False
        self._lcd.text_direction = self._lcd.LEFT_TO_RIGHT

        super().__init__(0.0)
    def _update_cursor(self):
        if not self._cursor:
            self._lcd.cursor = False
            self._lcd.blink = False
        else:
            self._lcd.cursor = True
            self._lcd.blink = True
            self._lcd.cursor_position(self._cursor_pos[0], self._cursor_pos[1])
    def set_contrast(self, value):
        if not self._vo:
            return
        value = min(max(value, 0.0), 1.0)
        self._vo.duty_cycle = int((2**16-1)*value)
    def _write(self, value, length=None, right_aligned=False, column=0, row=0):
        if not length:
            length = self._columns
        if type(value) is float:
            value = "{:.2f}".format(value)
        self._lcd.cursor_position(column, row)
        self._lcd.message = truncate_str(str(value), length, right_aligned)
        self._update_cursor()
    def deinit(self):
        del self._lcd
        del self._rs
        del self._en
        del self._d7
        del self._d6
        del self._d5
        del self._d4

        super().deinit()

class DisplayCharacterLCD_1602(DisplayCharacterLCD):
    def __init__(self, rs, en, d4, d5, d6, d7, vo=None, contrast=0.5):
        super().__init__(rs, en, d4, d5, d6, d7, 16, 2, vo, contrast)
    def set_title(self, text):
        self._write(text, self._columns-6, False, 0, 0)
    def set_group(self, text):
        self._write(text, 6, True, self._columns-6, 0)
    def set_value(self, text):
        self._write(text, self._columns, False, 0, 1)
    def set_selected(self, value):
        if value:
            self.show_cursor(0, 1)
        else:
            self.hide_cursor()
    def set_save_index(self, i):
        if i == 0:
            self.show_cursor(self._columns-2, 0)
        else:
            self.show_cursor((i-1)%self._columns, 1)

class DisplayCharacterLCD_1604(DisplayCharacterLCD):
    def __init__(self, rs, en, d4, d5, d6, d7, vo=None, contrast=0.5):
        super().__init__(rs, en, d4, d5, d6, d7, 16, 4, vo, contrast)
    def set_title(self, text):
        self._write(text, row=1)
    def set_group(self, text):
        self._write(text, row=0)
    def set_value(self, text):
        self._write(text, row=3)
    def set_selected(self, value):
        if value:
            self.show_cursor(0, 3)
        else:
            self.hide_cursor()
    def set_save_index(self, i):
        if i == 0:
            self.show_cursor(0, 0)
        else:
            self.show_cursor((i-1)%self._columns, 3)

def get_display():
    type = os.getenv("DISPLAY_TYPE","1602")
    if type == "1602":
        return DisplayCharacterLCD_1602(
            rs=getenvgpio("DISPLAY_RS"),
            en=getenvgpio("DISPLAY_EN"),
            d4=getenvgpio("DISPLAY_D4"),
            d5=getenvgpio("DISPLAY_D5"),
            d6=getenvgpio("DISPLAY_D6"),
            d7=getenvgpio("DISPLAY_D7"),
            vo=getenvgpio("DISPLAY_VO"),
            contrast=getenvfloat("DISPLAY_CONTRAST",0.25)
        )
    elif type == "1604":
        return DisplayCharacterLCD_1604(
            rs=getenvgpio("DISPLAY_RS"),
            en=getenvgpio("DISPLAY_EN"),
            d4=getenvgpio("DISPLAY_D4"),
            d5=getenvgpio("DISPLAY_D5"),
            d6=getenvgpio("DISPLAY_D6"),
            d7=getenvgpio("DISPLAY_D7"),
            vo=getenvgpio("DISPLAY_VO"),
            contrast=getenvfloat("DISPLAY_CONTRAST",0.25)
        )
    else:
        return Display() # Dummy display
