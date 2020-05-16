from __future__ import print_function
import RPi.GPIO as GPIO
import time

#Class for the SN74HC595 shift register

# Pin diagram
#        __ __
#  QB 1 |  U  | 16 VCC
#  QC 2 |     | 15 QA
#  QD 3 |     | 14 SER
#  QE 4 |     | 13 OE
#  QF 5 |     | 12 RCLK
#  QG 6 |     | 11 SRCLK
#  QH 7 |     | 10 SRCLR
# GND 8 |_____|  9 QH'
#     
# QA-H  - output
# Vcc   - 3V3 input
# SER   - Serial input (this is the value that will be placed in the register)
# OE    - Enable output (Low = enabled)
# RCLK  - Latch. Pull up to update output to what is stored on the registers
# SRCLK - Clock. When pulled up register will be shifted and the value of SER
#         will be placed into the register
# SRCLR - Clear register (low = clear)
# QH'   - Serial output (allows chips to be daisychained together)
# GND   - Ground

class SN74HC595:
    def __init__(self,data,latch,clock,chain=1,invert=False):
        # If no GPIO modes have been set up, we use BCM
        if GPIO.getmode() != GPIO.BCM:
                        print("SN74HC595: Warning: GPIO mode will be set to BCM")
                        GPIO.setmode(GPIO.BCM)
        # number of chips we have chained together
        self.chain=chain
        
        # this flag is set to true if we want to invert (i.e. 1 -> 0) the outputs
        self.invert=invert
        
        self.data=data
        self.latch=latch
        self.clock=clock
        
        GPIO.setup(self.data,GPIO.OUT)
        GPIO.setup(self.latch,GPIO.OUT)
        GPIO.setup(self.clock,GPIO.OUT)
        
        GPIO.output(self.data,GPIO.LOW)
        GPIO.output(self.latch,GPIO.LOW)
        GPIO.output(self.clock,GPIO.LOW)
        
        self.finalised=False
        
        
    
    # Update the output to what is stored in the register
    def update_output(self):
        if self.finalised:
            print("SN74HC595: Error, this instance is finalised. Doing nothing")
            return
        GPIO.output(self.latch,GPIO.LOW)
        time.sleep(0.0001)
        GPIO.output(self.latch,GPIO.HIGH)
        
    # Set the values of the outputs (does not update what is being displayed,
    # ...to do this use update_output)
    def set_output(self,values):
        if self.finalised:
            print("SN74HC595: Error, this instance is finalised. Doing nothing")
            return
        if self.invert: values=~values
        for i in range(8*self.chain):
            #ensure clock is pulled down
            GPIO.output(self.clock,GPIO.LOW)
            #set the new value
            GPIO.output(self.data,values&1)
            #lift the clock up to update the value and shift the register on by 1
            GPIO.output(self.clock,GPIO.HIGH)
            
            #shift 'values' by 1 byte
            values >>=1
        GPIO.output(self.clock,GPIO.LOW)
        
    # Clear the outputs and free the GPIO pins
    def finalise(self):
        print("SN74HC595: Finalising")
        self.set_output(0)
        if self.invert == False:
            GPIO.output(self.data,GPIO.LOW)
        else:
            GPIO.output(self.data,GPIO.HIGH)
        
        GPIO.output(self.clock,GPIO.LOW)
        GPIO.output(self.latch,GPIO.LOW)
        GPIO.cleanup(self.clock)
        GPIO.cleanup(self.latch)
        GPIO.cleanup(self.data)
        self.finalised = True
        

