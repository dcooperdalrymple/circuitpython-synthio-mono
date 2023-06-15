DEVICE = /media/$(USER)/CIRCUITPY/
LIBDIR = lib/rpi_pico_synthio
PATCHDIR = patches

SRCS := code.py config.json menu.json splash.bmp

upload: lib src patches

lib: $(LIBDIR)/*
	@for file in $^ ; do \
		echo $${file} "=>" $(DEVICE)$${file} ; \
		cp $${file} $(DEVICE)$${file} ; \
	done

src: $(SRCS)
	@for file in $^ ; do \
		echo $${file} "=>" $(DEVICE)$${file} ; \
		cp $${file} $(DEVICE)$${file} ; \
	done

patches: $(PATCHDIR)/*
	@for file in $^ ; do \
		echo $${file} "=>" $(DEVICE)$${file} ; \
		cp $${file} $(DEVICE)$${file} ; \
	done
