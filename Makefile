DEVICE = /media/$(USER)/CIRCUITPY/
MPYCROSS = ./tools/mpy-cross

LIBDIR = lib
SRCDIR = src
PATCHDIR = patches
WAVDIR = waveforms

SRCS := settings.toml boot.py code.py midi.json

LIB_SRCS := $(SRCDIR)/global.py $(SRCDIR)/display.py $(SRCDIR)/encoder.py $(SRCDIR)/midi.py $(SRCDIR)/audio.py $(SRCDIR)/synth.py $(SRCDIR)/waveforms.py $(SRCDIR)/voice.py $(SRCDIR)/keyboard.py $(SRCDIR)/arpeggiator.py $(SRCDIR)/parameters.py $(SRCDIR)/patches.py $(SRCDIR)/menu.py
LIB_PY = $(LIBDIR)/synthio_mono.py
LIB_MPY = $(LIBDIR)/synthio_mono.mpy

all: upload

clean:
	@rm $(LIB_PY) || true
	@rm $(LIB_MPY) || true

upload: clean $(LIB_MPY) lib src patches waveforms

update: clean $(LIB_MPY) mpy_update src

compile: clean $(LIB_MPY)

lib: $(LIBDIR)/*
	@mkdir -p $(DEVICE)$(LIBDIR) || true
	@for file in $^ ; do \
		echo $${file} "=>" $(DEVICE)$${file} ; \
		cp $${file} $(DEVICE)$${file} -r ; \
	done
	@rm $(DEVICE)$(LIB_PY) || true

src: $(SRCS)
	@for file in $^ ; do \
		echo $${file} "=>" $(DEVICE)$${file} ; \
		cp $${file} $(DEVICE)$${file} ; \
	done

patches: $(PATCHDIR)/*
	@mkdir -p $(DEVICE)$(PATCHDIR) || true
	@for file in $^ ; do \
		echo $${file} "=>" $(DEVICE)$${file} ; \
		cp $${file} $(DEVICE)$${file} ; \
	done

waveforms: $(WAVDIR)/*
	@mkdir -p $(DEVICE)$(WAVDIR) || true
	@for file in $^ ; do \
		echo $${file} "=>" $(DEVICE)$${file} ; \
		cp $${file} $(DEVICE)$${file} ; \
	done

$(LIB_PY):
	cat $(LIB_SRCS) >> $@

$(LIB_MPY): $(LIB_PY)
	$(MPYCROSS) -o $@ $<

mpy_update:
	@echo $(LIB_MPY) "=>" $(DEVICE)$(LIB_MPY)
	@cp $(LIB_MPY) $(DEVICE)$(LIB_MPY)
