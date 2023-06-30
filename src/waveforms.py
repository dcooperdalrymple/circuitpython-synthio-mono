class Waveform:
    def __init__(self, name, data):
        self.name = name
        self.data = data
    def deinit(self):
        del self.data

class Waveforms:
    def __init__(self, samples=256, amplitude=12000, dir="/waveforms"):
        self._samples = samples
        self._amplitude = amplitude
        self._dir = dir
        self._items = [
            Waveform("saw", numpy.linspace(self._amplitude, -self._amplitude, num=self._samples, dtype=numpy.int16)),
            Waveform("square", numpy.concatenate((numpy.ones(self._samples//2, dtype=numpy.int16)*self._amplitude,numpy.ones(self._samples//2, dtype=numpy.int16)*-self._amplitude))),
            Waveform("sine", numpy.array(numpy.sin(numpy.linspace(0, 4*numpy.pi, self._samples, endpoint=False)) * self._amplitude, dtype=numpy.int16)),
            Waveform("noise", numpy.array([random.randint(-self._amplitude, self._amplitude) for i in range(self._samples)], dtype=numpy.int16))
        ]

        # Append custom waveforms
        filenames = self._list_wav()
        if filenames:
            for filename in filenames:
                self._items.append(Waveform(self._get_wav_name(filename), self._read_wav_data(filename)))

    def get(self, value):
        if type(value) is str:
            for item in self._items:
                if item.name == value:
                    return item
        elif type(value) is int:
            return self._items[value]
        return None
    def get_list(self):
        arr = []
        for item in self._items:
            arr.append(item.name)
        return arr
    def get_index(self, name):
        for i in range(len(self._items)):
            if self._items[i].name == name:
                return i
        return 0
    def get_data(self, name):
        item = self.get(name)
        if not item:
            return None
        return item.data

    def _read_wav_data(self, filename):
        import adafruit_wave
        data = None
        with adafruit_wave.open(self._dir+"/"+filename) as w:
            if w.getsampwidth() == 2 and w.getnchannels() == 1:
                # Read into numpy array, resize (with linear interpolation) into designated buffer size, and normalize
                data = numpy.frombuffer(w.readframes(w.getnframes()), dtype=numpy.int16)
                data = numpy.array(numpy.interp(numpy.linspace(0,1,self._samples), numpy.linspace(0,1,data.size), data), dtype=numpy.int16)
                norm = max(numpy.max(data), abs(numpy.min(data)))
                if norm:
                    data = numpy.array(data*(self._amplitude/norm), dtype=numpy.int16)
            else:
                print("Failed to read {}: unsupported format".format(filename))
        free_module(adafruit_wave)
        del adafruit_wave
        return data
    def _valid_wav_filename(self, filename):
        return len(filename) > len("a.wav") and filename[-4:] == ".wav"
    def _get_wav_name(self, filename):
        if not self._valid_wav_filename(filename):
            return ""
        return str(filename[:-4])
    def _list_wav(self):
        try:
            return [filename for filename in os.listdir(self._dir) if self._valid_wav_filename(filename)]
        except:
            return []

    def deinit(self):
        for item in self._items:
            item.deinit()
        del self._items
