#!/usr/bin/env python
from __future__ import print_function
import numpy as np
import smbus
import time

# Class to control the PCF8591 analogue to digital converter
# Connects to the pi via i2c

#command structure:
#0x0AMM0IXX
# A  = analogue output (best to turn this on*)
# MM = output mode:
#        00 - 4 standard inputs
#        01 - 3 differential
#        10 - 1 diff, 2 normal
#        11 - two differential
# I  = Auto increment**
# NN = pin number (0-3)
#
# *  Analogue input forces the onboard oscillator to operate,
#    otherwise the chip needs ~1s to start up before it takes
#    sensible readings (see also **)
# ** The onboard oscillator is needed to stabilise auto-increment,
#    Therefore you should have analogue output on when using auto
#    increment


# Pin diagram
#          __ __
#  AIN0 1 |  U  | 16 VDD
#  AIN1 2 |     | 15 AOUT
#  AIN2 3 |     | 14 VREF
#  AIN3 4 |     | 13 AGND
#  A0   5 |     | 12 EXT
#  A1   6 |     | 11 OSC
#  A2   7 |     | 10 SCL
#  VSS  8 |_____|  9 SDA
#
# AIN0-3 - Analogue inputs
# A0-3   - Modify i2c address (ground to keed default address)
# VSS    - ground
# SDA    - SDA on pi
# SCL    - SCL on pi
# OSC    - disconnected
# EXT    - ground
# AGND   - ground
# VREF   - reference voltage
# AOUT   - Analogue output
# VDD    - 3v3


class PCF8591:
    def __init__(self,address=0x48,bus=None):
        print("PCF8591: Initialising with i2c address: %x"%address)
        #set up bus
        if bus == None:
            self.bus=smbus.SMBus(1)
        else: #use user-supplied bus
            self.bus=bus
            
        self.address=address
        self.finalised=False
        
        #start with a blank command. This is added to later
        self.command = 0b00000000
        
        # turn the analogue output on (see * and ** for justification)
        self.set_analogue_output(True)
        
    # set the input mode 0-3 (see description above)
    def set_input_mode(self,n):
        if self.finalised:
            print("Error: this PCF8591 instance is finalised. Doing nothing")
            return
        if n <= 3:
            self.command &= 0b11001111
            self.command |= (n<<4)
            
            print("PCF8591: Setting input mode to %d"%n)
            self.bus.write_byte(self.address, self.command)
        else:
            print("Error: Invalid input mode requested. Doing nothing.")
            
    #Set the channel (0-3) to read from    
    def set_input_channel(self,n):
        if self.finalised:
            print("Error: this PCF8591 instance is finalised. Doing nothing")
            return
        if n <= 3:
            self.command &= 0b11111100
            self.command  |=n
            print("PCF8591: Setting input channel to %d"%n)
            #tell it the channel, and read the stale data from it
            dum=self.bus.read_byte_data(self.address,self.command)
        else:
            print("Error: Invalid input channel selected. Doing nothing.")
            
    #get a reading from the selected channel
    def read(self):
        return self.bus.read_byte(self.address)
    
    # Turn on/off analogue output
    def set_analogue_output(self,onoff):
        if self.finalised:
            print("Error: this PCF8591 instance is finalised. Doing nothing")
            return
        if onoff == True:
            print("PCF8591: Enabling Analogue output")
            self.command |= 0b01000000
        else:
            print("PCF8591: Disabling Analogue output")
            self.command &= 0b10111111
        self.bus.write_byte(self.address,self.command)
    
    # Set the analogue value to be produced
    def set_output_value(self,value):
        if self.finalised:
            print("Error: this PCF8591 instance is finalised. Doing nothing")
            return
        if value < 256:
            self.bus.write_byte_data(self,address,value)
        else:
            print("Error: Invalid output value. Doing nothing")
    
    # Set the chip to auto increment the input channel
    def set_auto_increment(self,onoff):
        if self.finalised:
            print("Error: this PCF8591 instance is finalised. Doing nothing")
            return
        if (self.command & 0b01000000 == 0 and onoff):
            print("Warning: If enabling auto increment it is **strongly** advised to enable analogue output")
        if onoff == True:
            print("PCF8591: Enabling auto-increment")
            self.command |= 0b00000100
        else:
            print("PCF8591: Disabling auto-increment")
            self.command &= 0b11111011
        self.bus.write_byte(self.address,self.command)
    
    #reset the chip to its default state
    def reset(self):
        if self.finalised:
            print("Error: this PCF8591 instance is finalised. Doing nothing")
            return
        print("PCF8591: Resetting internal register")
        self.command=0b00000000
        self.bus.write_byte(self.address,self.command)
        
    # finalise the class
    def finalise(self):
        if self.finalised:
            print("This PCF8591 instance is already finalised. Doing nothing")
            return
        print("PCF8591: Finalised")
        self.bus.close()
        self.finalised=True
        

#test code            
if __name__ == "__main__":
    import matplotlib.pyplot as plt

    try:
        adc=PCF8591()
        adc.set_input_mode(0)
        
        adc.set_input_channel(0)
        
        vals=[]
        t=[]
        t0=time.time()
        t1=t0
        print("Reading for 1 second...")
        while t1-t0 < 1.:
            t1=time.time()
            vals.append(adc.read())
            t.append(t1-t0)
            #time.sleep(0.0)
        t=np.asarray(t)
        dt = t[1:] - t[0:-1]
        print("mean sampling time is: %f ms"%(np.mean(dt)*1000.))
            
        print("Plotting signal")
        plt.plot(t,vals)
        plt.show()
        
        
        print("")
        print("Now going to read all 4 inputs using auto-increment")
        
        
        
        adc.set_auto_increment(True)
        adc.set_input_channel(0)
        
        while True:
            f1=adc.read()
            f2=adc.read()
            f3=adc.read()
            f4=adc.read()
            print(f1, f2, f3, f4)
            time.sleep(0.2)

            
    finally:
        print("Closing bus")
        adc.finalise()
        
    
    
    
