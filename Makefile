DEVICE = /media/$(USER)/CIRCUITPY/
LIBDIR = lib
PATCHDIR = patches

SRCS := code.py parameters.json menu.json midi.json

all: update

upload: lib src patches

update: src

lib: $(LIBDIR)/*
	@mkdir $(DEVICE)$(LIBDIR) || true
	@for file in $^ ; do \
		echo $${file} "=>" $(DEVICE)$${file} ; \
		cp $${file} $(DEVICE)$${file} -r ; \
	done

src: $(SRCS)
	@for file in $^ ; do \
		echo $${file} "=>" $(DEVICE)$${file} ; \
		cp $${file} $(DEVICE)$${file} ; \
	done

patches: $(PATCHDIR)/*
	@mkdir $(DEVICE)$(PATCHDIR) || true
	@for file in $^ ; do \
		echo $${file} "=>" $(DEVICE)$${file} ; \
		cp $${file} $(DEVICE)$${file} ; \
	done
