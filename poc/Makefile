BINFOLDER=./build
INCFOLDER=./include
SRCFOLDER=./src

CC=gcc
CFLAGS=-O2 -I$(INCFOLDER) -Wall

CORE=1

.PHONY: all start_spectrem_cf start_spectrem_ins start_meltemdown_ins stop_spectrem_cf stop_spectrem_ins stop_meltemdown

all: build/spectrem_cf build/spectrem_ins build/meltemdown

build/spectrem_cf: $(SRCFOLDER)/spectrem/spectrem_cf.c
	@mkdir -p $(BINFOLDER)
	$(CC) $(CFLAGS) -o $(BINFOLDER)/spectrem_cf $(SRCFOLDER)/spectrem/spectrem_cf.c

build/spectrem_cf_noflush: $(SRCFOLDER)/spectrem/spectrem_cf_noflush.c
	@mkdir -p $(BINFOLDER)
	$(CC) $(CFLAGS) -o $(BINFOLDER)/spectrem_cf_noflush $(SRCFOLDER)/spectrem/spectrem_cf_noflush.c

build/spectrem_ins: $(SRCFOLDER)/spectrem/spectrem_ins.c
	@mkdir -p $(BINFOLDER)
	$(CC) $(CFLAGS) -o $(BINFOLDER)/spectrem_ins $(SRCFOLDER)/spectrem/spectrem_ins.c

build/meltemdown: $(SRCFOLDER)/meltemdown/meltemdown.c $(SRCFOLDER)/meltemdown/sregs.S
	@mkdir -p $(BINFOLDER)
	$(CC) $(CFLAGS) -o $(BINFOLDER)/meltemdown $(SRCFOLDER)/meltemdown/meltemdown.c $(SRCFOLDER)/meltemdown/sregs.S

start_spectrem_cf: build/spectrem_cf
	taskset -c $(CORE) ./build/spectrem_cf &

start_spectrem_cf_noflush: build/spectrem_cf_noflush
	taskset -c $(CORE) ./build/spectrem_cf_noflush &

start_spectrem_ins: build/spectrem_ins
	taskset -c $(CORE) ./build/spectrem_ins &

start_meltemdown: build/meltemdown
	taskset -c $(CORE) ./build/meltemdown &

stop_spectrem_cf:
	kill $$(pgrep spectrem_cf)

stop_spectrem_cf_noflush:
	kill $$(pgrep spectrem_cf)

stop_spectrem_ins:
	kill $$(pgrep spectrem_ins)

stop_meltemdown:
	kill $$(pgrep meltemdown)
