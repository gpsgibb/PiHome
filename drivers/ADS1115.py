#Code to operate a ADS1115 ananlgue to digital converter

from __future__ import print_function
import smbus
import time

#Address options for wiring:
#0x48 - ADDR to GND
#0x49 - ADDR to VDD
#0x50 - ADDR to SDA
#0x51 - ADDR to SCL

#default i2c channel and address
CHANNEL = 1
ADDRESS = 0x48

#addresses of the registers we need to read/write to/from
CONV_REG_ADDR = 0x00
CONFIG_REG_ADDR = 0x01

#Config register
# OS [15] 
# MUX [14:12]
# PGA [11:9]
# MODE [8]
# DR [7:5]
# COMP_MODE [4]
# COMP_POL [3]
# COMP_LAT [2]
# COMP_QUE [1:0]

# OS: (operational status)
#  0 - do nothing
#  1 - take single reading
OS = 0x00
#
# MUX: (input multiplexer - which pins we measure the voltage across)
#  000 - AIN0 and AIN1 (default)
#  001 - AIN0 and AIN3
#  010 - AIN1 and AIN3
#  011 - AIN2 and AIN3
#  100 - AIN0 and GND
#  101 - AIN1 and GND
#  110 - AIN2 and GND
#  111 - AIN3 and GND
MUX = 0x00
#
# PGA: (programmable gain amplifier - sets the voltage range it can measure in e.g. [-Vmax:Vmax])
#  000 - 6.144V
#  001 - 4.096V
#  010 - 2.048V (default)
#  011 - 1.024V
#  100 - 0.512V
#  101 - 0.256V
#  110 - 0.256V
#  111 - 0.256V
PGA=0x02
#
# MODE:
#  0 - continious conversion mode
#  1 - power down and wait for instructions (default)
MODE = 0x01
#
# DR: (data rate - how many measurements taken per second)
#  000 - 8/s
#  001 - 16/s
#  010 - 32/s
#  011 - 64/s
#  100 - 128/s (default)
#  101 - 250/s
#  110 - 475/s
#  111 - 860/s
DR = 0x04
#
# COMP_MODE (comparator mode - not used in this code):
#  0 - traditional (default)
#  1 - window
COMP_MODE=0x00
#
# COMP_POL (comparator polarity - not used in this code)
#  0 - active low
#  1 - active high
COMP_POL=0x00
#
# COMP_LAT (comparator latching - not used in this code)
#  0 - no latching (default)
#  1 - latching
COMP_LAT=0x00
#
# COMP_QUE (comparator queue - not used in this code)
#  00 - assert after one conversion
#  01 - assert after two conversions
#  10 - assert after four conversions
#  11 - off (default)
COMP_QUE = 0x03



class ADS1115():
    def __init__(self,channel=CHANNEL,address=ADDRESS):
        #sets all the values to the defaults as defined above
        self.channel = channel
        self.address = address
        self.OS=OS
        self.set_input(MUX,update_config=False)
        self.set_gain(PGA,update_config=False)
        self.MODE=MODE
        self.set_rate(DR,update_config=False)
        self.COMP_MODE=COMP_MODE
        self.COMP_LAT=COMP_LAT
        self.COMP_QUE=COMP_QUE
        
        #set up the communication bus
        self.bus = smbus.SMBus(self.channel)
        
        #send the configuration bytes to the device
        self._send_config()
        
    #gets a reading, returns the value in Volts
    def read(self):
        #if continuous read mode is on, just get the data from the register
        if self.MODE == 0:
            return self._read()
        #Instruct ADC to take a reading, then read the reading from the register
        else:
            self._send_config(1)
            
            return self._read()
    
    #sets the data rate. See above for the values
    def set_rate(self,dr,update_config=True):
        if dr < 0 or dr > 7:
            raise ValueError("Rate must be in the range [0:7]")
        self.DR = dr
        if dr == 0:
            self.rate = 8.
        elif dr == 1:
            self.rate = 16.
        elif dr == 2:
            self.rate = 32.
        elif dr == 3:
            self.rate = 64.
        elif dr == 4:
            self.rate = 128.
        elif dr == 5:
            self.rate = 250.
        elif dr == 6:
            self.rate = 475.
        else:
            self.rate = 860.
            
        #update the device's config    
        if update_config:
            self._send_config()
            
    def get_rate(self):
        return self.rate
    
    #Sets the input pins we are using. See above (MUX) for details    
    def set_input(self,mux,update_config=True):
        if mux < 0 or mux > 7:
            raise ValueError("Input must be between [0:7]")
        self.MUX = mux
        
        #update the device's config 
        if update_config:
            self._send_config()
        
    def get_input(self):
        return self.MUX
    
    #Sets the device mode. See above for details
    def set_mode(self,mode,update_config=True):
        if mode < 0 or mode > 1:
            raise ValueError("Mode must be 0 or 1")
        
        self.MODE=mode
        
        #update the device's config    
        if update_config:
            self._send_config()
        
    def get_mode(self):
        return self.MODE
     
    #Sets the gain of the device. See above for details (PGA) 
    def set_gain(self,gain,update_config=True):
        if gain > 7 or gain < 0:
            raise ValueError("Gain should be in the range [0:7]")
        self.PGA=gain
        if gain == 0:
            self.vmax = 6.144
        elif gain == 1:
            self.vmax = 4.096
        elif gain == 2:
            self.vmax = 2.048
        elif gain == 3:
            self.vmax= 1.024
        elif gain == 4:
            self.vmax = 0.512
        else:
            self.vmax = 0.256
        #update the device's config
        if update_config:
            self._send_config()
        
    def get_vmax(self):
        return self.vmax
    
    #takes the latest reading from the register and converts it to volts    
    def _read(self):
        #sleep to ensure the reading has been made
        time.sleep(1./self.rate)# + 0.0005)
        
        vals = self.bus.read_i2c_block_data(self.address,CONV_REG_ADDR,2)
        
        #combine the bytes into a uint
        val = (vals[0]<<8)|(vals[1])
        
        #convert to signed int (two's compliment)
        if val >= 0x8000:
            val = val - 0x10000
       
        val = float(val)/0x8000
        
        #convert to Volts
        val *=self.vmax
        
        return val
    
    #sends the config bytes to the device
    def _send_config(self,OS=OS):
        config=[OS<<7|self.MUX<<4|self.PGA<<1|self.MODE,
                    self.DR<<5|self.COMP_MODE<<3|self.COMP_LAT<<2|self.COMP_QUE]
            
        self.bus.write_i2c_block_data(self.address,CONFIG_REG_ADDR,config)
        
        
#quick test code        
if __name__ == "__main__":        
    
    #create the object
    adc = ADS1115()
    print(adc.read())
    
    #Tell it to take continuous measurements with a certain rate
    adc.set_mode(0)
    adc.set_rate(7)

    t0=time.time()
    t=[]
    v=[]
    for i in range(100):
        val = adc.read()
        t1=time.time()-t0
        t.append(t1)
        v.append(val)
    for i in range(100):
        print("t = %.4f s | v = %f V"%(t[i],v[i]))

    dt = t[-1]/len(t)
    print('dt = %s s'%dt)
    
    #set it back to idle mode
    adc.set_mode(1)
