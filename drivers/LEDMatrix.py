from __future__ import print_function
import numpy as np
import smbus
import time

address=0x70

#Class to control the HT16K33 chip in an adafruit 16x8 led matrix
#
# This chip drives the LED display (including multiplexing), thus
# taking a computational load off the pi. All the pi must do is specify
# what is to be displayed.
# 
# The HT16K33 communicates with the pi over the i2c bus, with a default
# address of 0x70. The commands are:
#
# 0b0010000S - switch the internal oscillator on/off (S=1/0)
# 0b10000BBD - Set blink mode (BB) and turn display on/off (D)
#                B=0 - static
#                B=1 - 2Hz flash
#                B=2 - 1Hz flash
#                B=3 - 0.5Hz flash
# 0b1110BBBB - Set the brightness 0-15 (BBBB)
# 0b0000NNNN - Specify the set of 8 LEDs to write to (0-15)
#                (with sets 0 and 1 being the first and second set of
#                 8 LEDS in row 0, sets 2 and 3 being on row 1 etc)
#
# In this class, each row (16 LEDs = 2 sets of 8 LEDs) is represented
# as a single integer from 0 to 2**15. The class itself turns this into
# two bytes to be sent to the HT16K33
#
# The class contains a buffer which is an array of 8 16 bit integers,
# representing the 8 rows. This can either be externally specified
# using the "set_buffer" method, or the class's internal buffer can 
# be modified pixel by pixel using the "set_pixel" method.
#
# The buffer is written to the display using the "write_buffer" method.
#
# There are also methods for setting the brightness, blink, and
# scrolling the image on the screen up/down/left/right 
#
# NOTE: the pixels are numbered 0-15 in the x direction, so a value
# of 0b1 corresponds to the leftmost pixel, and a value of 2**15 is the
# right most pixel (i.e. opposite of how you write the num in binary)

class LEDMatrix:
    def __init__(self,address,bus=None):
        self.address = address
        
        #set up i2c bus
        if bus == None:
            print("LEDMatrix: creating i2c bus object")
            self.bus=smbus.SMBus(1)
        else:
            self.bus=bus
        
        #cache the display settings (screen on/off, blink)    
        self.display=0b10000000
            
        #initialise matrix (turn on internal oscillator)
        self.bus.write_byte(self.address,0b00100001)
        
        self.display_on(True)
        
        self.set_blink(0)
        
        self.set_brightness(8)
        
        #initialise the screen buffer
        self.buffer=[0,0,0,0,0,0,0,0]
        
        self.write_buffer()
    
    #set the display brightness (0-15)
    def set_brightness(self,val):
        cmd = 0b11100000
        if val >=0 and val <=15:
            self.bus.write_byte(self.address,cmd|val)
        else:
            print("LEDMatrix: Invalid brightness requested")
    
    #Set the blink rate of the display:
    #   0 - no blink
    #   1 - 2Hz
    #   2 - 1Hz
    #   3 - 0.5Hz
    def set_blink(self,blink):
        if blink >= 0 and blink <=3:
            self.display&=0b11111001
            self.bus.write_byte(self.address,self.display|(blink<<1))
        else:
            print("LEDMatrix: Invalid blink rate requested")
    
    #turn the screen on/off
    def display_on(self,onoff):
        self.display&=0b11111110
        if onoff:
            self.display |=1
            self.bus.write_byte(self.address,self.display)
            
        else:
            self.display |=0
            self.bus.write_byte(self.address,self.display)
        
    
    #write the buffer to the display (i.e. update display)
    def write_buffer(self):
        for row in range(8):
            i=2*row
            self.bus.write_byte_data(self.address,i+1,self.buffer[row]>>8)
            self.bus.write_byte_data(self.address,i,self.buffer[row])
             
    
    #set the image buffer according to externally applied buffer
    def set_buffer(self,buffer):
        if len(buffer) == 8:
            self.buffer=buffer
        else:
            print("LEDMatrix: Invalid buffer length specified")
    
    # inverts the buffer so 0 <-> 1
    def invert_buffer(self):
        for i in range(8):
            self.buffer[i] = ~self.buffer[i]
        
    
    #set a pixel value in the buffer
    # (x,y)=(0,0) is the lower left corner
    def set_pixel(self,x, y,val):
        if (y >=0 and y <8) and (x>=0 and x < 16):
            #set a mask which is 1 except for at x
            mask = ~(1<<(x))
            #mask the row so the location at x is zero
            self.buffer[7-y] &=mask
            #put a 1 in the location of x if val=1
            if val==1:
                mask = ~mask
                self.buffer[7-y] |=mask
        else:
            print("LEDMatrix: Invalid x or y specified")
            
    # Inverts a pixel's value
    def invert_pixel(self,x,y):
        if (y >=0 and y <8) and (x>=0 and x < 16):
            mask = 1<<x
            if self.buffer[7-y]&mask > 0:
                self.buffer[7-y] &= (~mask)
            else:
                self.buffer[7-y] |= mask
        else:
            print("LEDMatrix: Invalid x or y specified")
    
    #queries a pixel's value
    def query_pixel(self,x,y):
        if (y >=0 and y <8) and (x>=0 and x < 16):
            mask = 1<<x
            if self.buffer[7-y]&mask > 0:
                return 1
            else:
                return 0
        else:
            print("LEDMatrix: Invalid x or y specified")
    
    #shifts the buffer up by one pixel        
    def shift_up(self,periodic=True):
        if periodic:
            buff = self.buffer[0]
        for i in range(7):
            self.buffer[i] = self.buffer[i+1]
        if periodic:
            self.buffer[7] = buff
        else:
            self.buffer[7]=0
    
    #shifts the buffer down by one pixel
    def shift_down(self,periodic=True):
        if periodic:
            buff = self.buffer[7]
        for i in range(7,0,-1):
            self.buffer[i] = self.buffer[i-1]
        if periodic:
            self.buffer[0] = buff
        else:
            self.buffer[0] = 0
    
    #shifts the buffer left by one pixel        
    def shift_left(self,periodic=True):
        if periodic:
            buf=[]
            for i in range(8):
                buf.append(self.buffer[i]&1)
        for i in range(8):
            self.buffer[i]>>=1
        if periodic:
            for i in range(8):
                self.buffer[i] |= (buf[i]<<15)
    
    #shifts the buffer right by one pixel
    def shift_right(self,periodic=True):
        if periodic:
            buf=[]
            for i in range(8):
                buf.append((self.buffer[i]>>15)&1)
        for i in range(8):
            self.buffer[i]<<=1
        if periodic:
            for i in range(8):
                self.buffer[i] |= buf[i]
    
    #clears the buffer            
    def clear_buffer(self):
        self.buffer=[0,0,0,0,0,0,0,0]
    
    
    
            
        
        
    
            
    
    def finalise(self):
        cmd = 0b00100000
        self.bus.write_byte(self.address,cmd)    
        
            
        
if __name__ == "__main__":
    

    matrix=LEDMatrix(address=0x70)
    
    #buff=[0,0,0,0b0110011001010101,0,0,0,0]
    
    matrix.set_brightness(0)
    
    matrix.invert_buffer()
    matrix.write_buffer()
    time.sleep(1)
    matrix.invert_buffer()
    
    #make two squares on left and right hand panels
    matrix.set_pixel(4,6,1)
    matrix.set_pixel(5,6,1)
    matrix.set_pixel(4,5,1)
    matrix.set_pixel(5,5,1)
    
    matrix.set_pixel(9,3,1)
    matrix.set_pixel(10,3,1)
    matrix.set_pixel(9,4,1)
    matrix.set_pixel(10,4,1)
    matrix.write_buffer()
    
    #make them scroll up, down, left, right
    time.sleep(1)
    for i in range(16):
        matrix.shift_up()
        matrix.write_buffer()
        time.sleep(0.1)
    for i in range(16):
        matrix.shift_down()
        matrix.write_buffer()
        time.sleep(0.1)
    for i in range(16):
        matrix.shift_left()
        matrix.write_buffer()
        time.sleep(0.1)
    for i in range(16):
        matrix.shift_right()
        matrix.write_buffer()
        time.sleep(0.1)
        
    #invert the screen
    matrix.invert_buffer()
    matrix.write_buffer()
    time.sleep(1)
    matrix.invert_buffer()
    matrix.write_buffer()
    time.sleep(1)
    matrix.invert_buffer()
    matrix.write_buffer()
    time.sleep(1)
    matrix.invert_buffer()
    matrix.write_buffer()
    time.sleep(1)
    
    #clear the display    
    matrix.clear_buffer()
    matrix.write_buffer()
    time.sleep(1)
    
    #display random points being randomly turned off and on
    for i in range(10):
        for i in range(8):
            x=np.random.randint(0,16)
            y=np.random.randint(0,8)
            matrix.invert_pixel(x,y)
        matrix.write_buffer()
        time.sleep(0.5)
 
    #ramp brightness up then down again
    for i in range(16):
        matrix.set_brightness(i)
        time.sleep(0.2)
    for i in range(15,-1,-1):
        matrix.set_brightness(i)
        time.sleep(0.2)
        
    # cycle though blink settings    
    for i in range(4):
        matrix.set_blink(i)
        time.sleep(4)
        
    #invert the buffer
    matrix.display_on(False)
    
    
    
    
    
    
    
