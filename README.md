# PiHome
Code for my DIY Raspberry Pi based smart home system

Currently a work in progress, but the plan is to have a number of Raspberry
Pis about my flat recording data (temperature, humidity, electricity/gas/water
usage etc...) which will be available in a central place. I also have plans
for creating a smart-thermostat using a raspberry pi.

The `drivers` and `sensors` directories contain code to drive some chips and read data from some sensors.

The `utils` directory contains code to log sensor data to a sqlite database (and older code that logs the data to plain text files)

The `www` directory contains code for a flask-based webapp that displays info about the Pi, and allows you to browse data collected from its sensors
 
The file `clock.py` controls a "smart" bedside clock that measures, logs and displays the temperature and humidity of my bedroom.

The `website.py` file is the entry point for the website