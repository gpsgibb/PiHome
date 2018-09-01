LDFLAGS = $(shell python-config --cflags) -lwiringPi
CFLAGS = $(shell python-config --ldflags)

C: DHT.c
	gcc $(LDFLAGS) $(CFLAGS) DHT.c -o DHT

python: 
	python setup.py install

all: C python
