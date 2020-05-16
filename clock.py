# -*- coding: UTF-8 -*-
#!/usr/bin/env python
from __future__ import print_function
import numpy as np
import time
import json
import datetime
import traceback

from utils import logger, GetConfig
import drivers
import sensors


#This code uses a Adafruit 16x8 LED matrix to act as a clock, with an
#added DHT sensor to record and display the temperature and humidity.
#
#The bottom 5 rows display the time via 4 numeric digits. The top 2
#rows encode the temperature and humidity via groups of dots.
#
# The temperature is encoded on the left panel, via two groups of dots.
# One for the 'tens' and one for the 'units'/ So the temperature 23' is
# represented by a group of 2 dots, then a group of 3.
#
# The Humidity is encoded on the right panel, via two groups of dots.
# The first group represents the 'tens' of the humidity, and the second
# group represents 2.5% of humidity, so a humidity of 65% is represented
# by 6 dots and 2 dots.
#
# For example, the time 23:45, 25'C and 73% humidity is shown as:
#
#   __ __ __ __ __ __ __ __ __ __ __ __ __ __ __ __
#  |##       ## ## ##      |## ## ## ##       ##   |
#  |##       ## ##         |## ## ##               |
#  |                       |                       |
#  |## ##       ## ##      |   ##          ## ## ##|
#  |      ##          ##   |   ##    ##    ##      |
#  |   ##       ## ##      |   ## ## ##    ## ##   |
#  |##                ##   |         ##          ##|
#  |## ## ##    ## ##      |         ##    ## ##   |
#   -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- 
#
#
#Dictionary containing arrays corresponding to the digits 0-9 on the 
#LED matrix
digit={}
digit[0] = [0b0000,
            0b0000,
            0b0000,
            0b0100,
            0b1010,
            0b1010,
            0b1010,
            0b0100]
            
digit[1] = [0b0000,
            0b0000,
            0b0000,
            0b1000,
            0b1100,
            0b1000,
            0b1000,
            0b1000]
            
digit[2] = [0b0000,
            0b0000,
            0b0000,
            0b0110,
            0b1000,
            0b0100,
            0b0010,
            0b1110]
            
digit[3] = [0b0000,
            0b0000,
            0b0000,
            0b0110,
            0b1000,
            0b0110,
            0b1000,
            0b0110]
            
digit[4] = [0b0000,
            0b0000,
            0b0000,
            0b0010,
            0b1010,
            0b1110,
            0b1000,
            0b1000]
            
digit[5] = [0b0000,
            0b0000,
            0b0000,
            0b1110,
            0b0010,
            0b0110,
            0b1000,
            0b0110]
            
digit[6] = [0b0000,
            0b0000,
            0b0000,
            0b1100,
            0b0010,
            0b0110,
            0b1010,
            0b0100]
            
            
digit[7] = [0b0000,
            0b0000,
            0b0000,
            0b1110,
            0b1000,
            0b0100,
            0b0010,
            0b0010]
            
digit[8] = [0b0000,
            0b0000,
            0b0000,
            0b1110,
            0b1010,
            0b1110,
            0b1010,
            0b1110]
            
digit[9] = [0b0000,
            0b0000,
            0b0000,
            0b1110,
            0b1010,
            0b1110,
            0b1000,
            0b1000]

#displays the 4 characters and temp/humidity data on the display
def display_chars(char1,char2,char3,char4,temp, hum,matrix):
    buffer=[0,0,0,0,0,0,0,0]
    
    #create the digits in the clock part of the display
    for row in range(8):
        buffer[row] = digit[char1][row]>>1
        buffer[row] += digit[char2][row]<<3
        buffer[row] += digit[char3][row]<<8
        buffer[row] += digit[char4][row]<<12
        
    #now create temperature part of display:
    temp=int(round(temp))
    
    #create dots for the 10s
    tens = (temp/10)%10
    buffer[0] |= ( 2**(tens/2 + tens%2)-1)
    buffer[1] |= (2**(tens/2) -1)
    
    units=temp%10 
    #create dots for the units:
    buffer[0] |= ( 2**(units/2 + units%2)-1) << 3 
    buffer[1] |= ( 2**(units/2)-1) << 3 
    
    #now create humidity part of display:
    
    #create dots for the 10s
    tens = int((hum/10)%10)
    buffer[0] |= ( 2**(tens/2 + tens%2)-1) << 8
    buffer[1] |= (2**(tens/2) -1) << 8
    
    
    units = hum%10
    quarters = int(round(units/2.5))
    #create dots for the units:
    buffer[0] |= ( 2**(quarters/2 + quarters%2)-1) << 14
    buffer[1] |= ( 2**(quarters/2)-1) << 14 
    
    
    #update display
    matrix.set_buffer(buffer)
    matrix.write_buffer()


if __name__ == "__main__":

    config = GetConfig(key="clock")

    refresh_rate = config["refresh_rate"]
    data_cadence = config["data_cadence"]

    interval = data_cadence/refresh_rate


    
    try:
        #setup LED matrix     
        matrix=drivers.LEDMatrix(address=0x70)
        matrix.set_brightness(0)
        matrix.set_blink(0)
        
        #set up DHT
        DHT=sensors.DHT(21,22)

    
        #set up logger
        logger.init()

         # logger=utils.Logger("TempHum",3,["Temperature","Humidity","Attempts"])
        
        #register temperature and humidity with the database
        logger.register_variable(name="Temperature",
                            unit= u"°C",
                            description="Bedroom Temperature",
                            min=15.0,
                            max=30.0)
        logger.register_variable(name="Humidity",
                            unit="%",
                            description="Bedroom Relative Humidity",
                            min=0.0,
                            max=100.0)
    
        
        #loop for the clock
        i=0
        while True:
            #Take temperature reading every 30 loops
            if i%interval == 0:
                result=DHT.read()
                if result["status"]==sensors.DHTsensor.SUCCESS:
                    temp=result["Temperature"]
                    hum=result["Humidity"]
                    attempts=result["tries"]+1
                    #logger.log(Temperature=temp,Humidity=hum,Attempts=attempts)
                    #register the data, opting to not recompute the statistics as we will do this at the end of the day
                    metadata = json.dumps({"attempts":attempts})

                    logger.register_reading(variable="Temperature",
                                            value = temp, 
                                            metadata = metadata)
                    logger.register_reading(variable="Humidity",
                                            value = hum, 
                                            metadata = metadata)

                    print(datetime.datetime.now(), temp, hum)
                else:
                   #if this has failed, display 0 for the temp and hum
                   temp=0
                   hum=0
                   print(result["status"], sensors.DHTsensor.SUCCESS)
            #get current time
            t=datetime.datetime.now()
            hh=int(t.hour)
            mm=int(t.minute)
            #update display
            display_chars((hh/10)%10,hh%10,(mm/10)%10,mm%10,temp, hum,matrix)
            i+=1
            time.sleep(refresh_rate)

    except Exception as e:
        print(e)
        traceback.print_exc()
        raise e
           
           
    finally:
    
        matrix.finalise()
        DHT.finalise()



            


