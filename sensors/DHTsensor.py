#!/usr/bin/env python
from __future__ import print_function
import numpy as np
import RPi.GPIO as GPIO
import time
import sys
import DHTC

# Class to read the DHT11/22 Temperature and Humidity sensor
# Uses either a C DHT reading library (method="C") or a Python one
# (method="Py")
#
# Wiring diagram:
#           ___________
#  3V3   --|_|_|_|_|_|_|
#  data* --|_|_|_|_|_|_|
#  none  --|_|_|_|_|_|_|
#  GND   --|_|_|_|_|_|_|
#  
# *The data line should be pulled up with a pullup resistor
#
# To read the DHT we need to pull the data line down for at least 18ms
# (then release) to signal that we wish to make a reading
# The DHT should then pull the line down for 80us to acknowledge receipt
# of the command, then release for 80us.
# The DHT will now send 5 bytes (40 bits) of data. Each bit will consist
# of a 50us pull down followed by a high of:
#    - 30us = 0
#    - 70us = 1
# Which corresponds to a gap between successive pulldowns of the data 
# line of 80us (0) or 120us (1). By timing the gaps we can therefore 
# read the data
# 
# The DHT's data consists of 2 bytes of humidity data, 2 bytes of 
# Temperature data, then a checksum where B0 + B1 + B2 + B3 = B4
# How the data is encoded depends on the DHT model:
# - DHT11:
#         The first byte corresponds to the whole number, and the second
#         byte corresponds to the part after the decimal point, e.g. if
#         the bytes are 25 and 52 then the value is 25.52
# - DHT22:
#         The two bytes together make a 16 bit binary number, equal to
#         10x the value, so if the bytes equal 315 then the value is 31.5
#
# NOTE: Reading the DHT requires precise timing. Due to operating system
# scheduling and interrupts, this can often go wrong. The DHT class 
# therefore will make several attempts at getting a reading if it is
# unsuccessful the first time.
#
# Note2: The reading from the DHT is stale (i.e. the reading at the time
# it was last read from. You therefore need to take two readings to get
# the current temperature and humidity
#
# **IMPORTANT**
# The DHT can only be read once every 1-2 seconds. Any more frequently 
# than this and the sensor can lock.
#
# 

# Success/error codes
INCORRECT_BYTES=1
NO_RESPONSE=2
INCORRECT_CHKSUM=3
SUCCESS=0

default="C"


class DHT:
    def __init__(self,pin,sensortype=None, method=default):
        # set the data pin
        self.pin=pin
        
        
        if method != "C" and method != "Py":
            print("Error: invalid reading method. Aborting")
            sys.exit()
        self.method=method
        
        if sensortype==None:
            print('Error no sensortype specified. Aborting')
            sys.exit()
        if (sensortype != 22 and sensortype != 11):
            print('Error: invalud sensortype specified. Aborting')
            sys.exit()
        self.sensortype = sensortype


        #make sure GPIO library is running. If not, set it up
        if GPIO.getmode() != GPIO.BCM:
            print("Warning: GPIO mode will be set to BCM")
            GPIO.setmode(GPIO.BCM)
    
        #set pin to output and high
        GPIO.setup(self.pin,GPIO.OUT)
        GPIO.output(self.pin,GPIO.HIGH)
        
        self.Hum=None
        self.Temp=None
        
        #old measurements
        self.oldHum=None
        self.oldTemp=None
        
        time.sleep(0.1)
    
    #checks if the readings we got seem sensible    
    def sanityCheck(self):
        
        #first test: see if the numbers are valid
        if self.Hum > 100:
            #clearly wrong as 0% < humidity <100%
            print("Invalid humidity (>100%)")
            return False
        
        if self.Temp > 40:
            #clearly wrong, it never gets above 40 degrees in Scotland!
            print("Invalid temperature - too hot!")
            return False
            
        #Second test: Check if there is an acceptable gradient (5% or 1')
        if self.oldTemp != None:
            print("Comparing with old measurements")
            if np.abs(self.oldTemp - self.Temp) > 1:
                print("Too large dT") 
                return False
                
            if np.abs(self.oldHum-self.Hum) > 5:
                print("Too large dH")
                return False
        
        #everything seemed to pass
        return True
        
        
    
    #Read (attempt to at least) from DHT and return result dictionary
    def read(self):
        tries=0
        statuses=[]
        
        
    
        while tries < 10:
            status=self.__get_data()
            statuses.append(status)
            if status == SUCCESS and self.sanityCheck():
                break
            else:
                print("Trying again in 3 seconds...")
                tries+=1
                time.sleep(3)
                
        dict={}
        dict["status"]=status
        dict["tries"]=tries
        dict["statuses"]=statuses				
        dict["Temperature"]=self.Temp
        dict["Humidity"]=self.Hum
        return dict
    
            

    #Get the last read temperature (does NOT read the temperature)
    def Get_Temp(self):
        return self.Temp

    #Get the last read humidity (does NOT read the humidity)
    def Get_Hum(self):
        return self.Hum

    # attempts to read from the DHT
    def __get_data(self):
        
        self.oldTemp=self.Temp
        self.oldHum=self.Hum
        
        if self.method == "C":
            print("Reading from C library")
            result=DHTC.read(self.pin,self.sensortype)
            self.Temp = result["Temperature"]
            self.Hum = result["Humidity"]
            return result["status"]
        else:
            print("Reading from python library")
            data=[]
    
            # send an initial low to signal we want data
            GPIO.output(self.pin,GPIO.LOW)
        
            #pause for some time (18ms is the minimum time)
            time.sleep(0.018)
            
            #bring pin up high again then set to input
            GPIO.setup(self.pin,GPIO.IN)
            
            #constantly poll GPIO, look for cases where signal drops (start of new bit transfer)
            #and measure when this happens
            t0=time.time()
            tm=0
            old=0
            while (tm < 0.006):
                tm=time.time()-t0
                new=GPIO.input(self.pin)
                if (new-old ==-1):
                    data.append(tm)
                old=new
            
            #revert GPIO pin to output and hold pin at high
            GPIO.setup(self.pin,GPIO.OUT)
            GPIO.output(self.pin,GPIO.HIGH)
            
            #Check we have the right amount of data
            # (We sometimes are lucky enough to measure the acnowledge
            #  pull down, so 41 or 42 timings are good, if 42 we ignore 
            #  the first one)
            if len(data) == 0:
                print("No data received from DHT")
                return NO_RESPONSE
            if (len(data) < 41 or len(data) >42):
                print("Bad data - read %d bits"%(len(data)-1))
                return INCORRECT_BYTES
            if (len(data) == 42): #if we're "lucky" enough to catch initial signal from DHT we want to prune this
                data=data[1:]
            
            
            #do some basic processing (get time interval and convert to micro seconds)
            data=np.asarray(data)
            if (len(data) > 1):
                data=data[1:]-data[0:-1]
                data=data*1E6
                
            
            #determine bits from time delays
            bits=np.zeros(40,dtype=int)
            for i in range(40):
                if data[i] > 100.:
                    bits[i]=1
            
            #parse stream of bits into bytes
            #[pressure1, pressure2, temp1, temp2, checksum]
            vals=[0,0,0,0,0]
            for i in range(40):
                if i%8==0: #start of new byte
                    x=0b10000000
                vals[i/8]+=bits[i]*x
                x>>=1
                
            #verify checksum: sum of first 4 bytes should equal last byte
            sum = vals[0]+vals[1]+vals[2]+vals[3]
            if sum&vals[4] != vals[4]:
                print("Incorret checksum :(")
                return INCORRECT_CHKSUM
            
            if self.sensortype == 11:
                self.Hum = vals[0] + 0.01*vals[1]
                self.Temp= vals[2]&0b01111111 + 0.01*vals[3]
            else:
                self.Hum = 0.1*( (vals[0]<<8)+vals[1])
                self.Temp = 0.1*( ((vals[2]&0b01111111)<<8 )+ vals[3])
            
            # test for negative temperature
            if vals[2]&0b10000000 == 128:
                self.Temp *= -1
            
            return SUCCESS
        
    def finalise(self):
        print("Finalising DHT")
        GPIO.cleanup(self.pin)
            


#example/test code	
if __name__ == "__main__":
    try:
        GPIO.setmode(GPIO.BCM)
    
        dht=DHT(pin=20,sensortype=22)
        
        result = dht.read()
        if result["status"] == SUCCESS:
            temp=result["Temperature"]
            hum=result["Humidity"]
            AT = temp +0.33*(hum/100. *6.105*np.exp(17.27*temp/(237.7+temp)))-4
            print("Temp= %2.1f 'C, Humidity=%2.1f%%, Apparent Temperature = %2.1f 'C"%(temp,hum,AT))
        else:
            print("Something went wrong :(")
            print("Error code: %d"%result["status"])
        
        
    finally:
        dht.finalise()





