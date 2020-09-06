#Reads the temperature, humidity and pressure from a Bosch BME280

#Basic usage:
#  Initialise with s = BME280()
#
#  Take a reading with s.read()
#
#  This returns a dictionary of the form:
#    {
#      "Pressure": {
#        "Unit": "mBar/hPa", 
#        "Value": 1011.55
#      }, 
#      "Temperature": {
#        "Unit": "Degrees Celsius", 
#        "Value": 21.84
#      }, 
#      "Humidity": {
#        "Unit": "% Relative Humidity", 
#        "Value": 48.74
#      }
#    }
#

from __future__ import print_function
import smbus
import time


#hard coded default values. Can be changed when instantiating the sensor class
CHANNEL=1
DEVICE_ADDRESS = 0x76

ID_ADDR = 0xd0
CTRL_HUM_ADDR = 0xF2
CTRL_MEAS_ADDR = 0xF4
DATA_ADDR = 0xF7
RESET_ADDR = 0xE0

#oversampling values (number of samples used when taking a measurement):
# 0 - do not take measurement
# 1 - 1
# 2 - 2
# 3 - 4
# 4 - 8
# 5 - 16

#oversampling defaults - >1 is probably overkill
T_OVERSAMPLE=3 #NOTE: Cannot be 0 as this is needed to calculate the others
P_OVERSAMPLE=3
H_OVERSAMPLE=3

RESET_VALUE = 0xB6

class BME280:
    def __init__(self,
                 channel=CHANNEL,
                 address=DEVICE_ADDRESS,
                 t_oversample=T_OVERSAMPLE,
                 p_oversample=P_OVERSAMPLE,
                 h_oversample=H_OVERSAMPLE
                 ):
        self.channel=channel
        self.address=address
        
        self.t_oversample = t_oversample
        self.p_oversample = p_oversample
        self.h_oversample = h_oversample
        
        #sanity checking the values  of t, h, p_oversample
        if self.t_oversample <= 0 or t_oversample > 5:
            raise ValueError("t_oversample must be in the range [1,5]")
        if self.h_oversample < 0 or h_oversample > 5:
            raise ValueError("h_oversample must be in the range [0,5]")
        if self.p_oversample < 0 or p_oversample > 5:
            raise ValueError("p_oversample must be in the range [0,5]")
        
        #set up the communication bus
        self.bus = smbus.SMBus(self.channel)
        
        #check the device returns the correct ID (0x60)
        self.id = self.bus.read_byte_data(self.address,ID_ADDR)
        
        if self.id != 0x60:
            raise ValueError("Incorrect device ID. Got 0x%x, should be 0x60"%self.id)
        
        # Get the conversion constants - needed to calculate T, P and H
        self._get_constants()
    
    #Take a reading
    def read(self):
        #set the ctrl_hum register (00000-hhh) = 00000-h_oversample
        ctrl_hum = self.h_oversample & 0xFF
        self.bus.write_byte_data(self.address,CTRL_HUM_ADDR,ctrl_hum)
       
        #set the ctrl_meas register (ttt-ppp-mm) = t_oversample - p_oversample - mset
        mset = 0x01 #0 = sleep mode, 1 or 2 = forced (manual) mode, 3 = normal (automatic) mode
        ctrl_meas = (self.t_oversample<<5)|(self.p_oversample<<2)|mset
        #This instructs the sensor to take a reading
        self.bus.write_byte_data(self.address,CTRL_MEAS_ADDR,ctrl_meas)
        
        #wait until the reading is completed
        self._wait_for_reading()
        
        #read the P, t and H data from the registers (8 registers in total)
        data=self.bus.read_i2c_block_data(self.address,DATA_ADDR,8)
        
        #re-arrange the bytes into 2 x 20 bit uints (P and T) and one ushort (H)
        p_raw = data[0]<<12|data[1]<<4|data[2]>>4
        t_raw = data[3]<<12|data[4]<<4|data[5]>>4
        h_raw = data[6]<<8|data[7]
        
        #calculate the dimensional values
        T=self._getT(t_raw) # degrees Centigrade
        P=self._getP(p_raw) # hPa/mBar
        H=self._getH(h_raw) # % relative humidity
        
        #dictionary to hold the results
        reading = {}
        
        reading["Temperature"] = {"Value":T,"Unit":"Degrees Celsius"}
        if P is not None:
            reading["Pressure"] = {"Value":P,"Unit":"mBar/hPa"}
        if H is not None:
            reading["Humidity"] = {"Value":H,"Unit":"% Relative Humidity"}
        
        return reading
    
    #resets the sensor
    def reset(self):
        #write the reset command to the reset register
        self.bus.write_byte_data(self.address,RESET_ADDR,RESET_VALUE)
        #sleep to make sure everything is reset (datasheet does not say how long a reset takes)
        time.sleep(0.1)
        
        
    #Calculates the temperature in degrees Centigrade (to 2 decimal places)    
    def _getT(self,t):
        v1 = (((t>>3)-(self.dig_T1<<1))*self.dig_T2)>>11
        v2 = ((((t>>4)-self.dig_T1)*((t>>4)-self.dig_T1))>>12)*(self.dig_T3)>>14
        self.tfine = v1+v2
        T = ((self.tfine*5 + 128) >> 8)/100.
        
        return T
    
    #Calculates the pressure in hPa/mBar (to 2 decimal places)
    def _getP(self,p):
        #exit if we are not collecting the pressure
        if self.p_oversample == 0:
            return None
        
        var1 = self.tfine - 128000
        var2 = var1 * var1 * self.dig_P6
        var2 = var2 + ((var1*self.dig_P5)<<17)
        var2 = var2 + ((self.dig_P4)<<35)
        var1 = ((var1 * var1 * self.dig_P3)>>8) + ((var1 * self.dig_P2)<<12)
        var1 = ((((1)<<47)+var1))*(self.dig_P1)>>33;
        if var1 == 0:
            print('Pressure error...')
            return 0
        P = 1048576-p
        P = (((P<<31)-var2)*3125)/var1
        var1 = ((self.dig_P9) * (P>>13) * (P>>13)) >> 25
        var2 = ((self.dig_P8) * P) >> 19
        P = ((P + var1 + var2) >> 8) + ((self.dig_P7)<<4)
        P=(P//256)/100.
        
        return P
    
    #Calculates the % relative humidity (2 decimal places)
    def _getH(self,h):
        if self.h_oversample == 0:
            return None
        v = self.tfine - 76800
        v = (((h << 14) - ((self.dig_H4) << 20) - ((self.dig_H5) * v)) + (16384) >> 15) * (((((((v * (self.dig_H6)) >> 10) * (((v * (self.dig_H3)) >> 11) + (32768))) >> 10) + ((2097152)) * (self.dig_H2) + 8192) >> 14 ))
        v = (v - (((((v >> 15) * (v >> 15)) >> 7) * (self.dig_H1)) >> 4))
        if v < 0:
            v = 0
        if v > 419430400:
            v = 419430400
        H = (v >> 12 )/1024.
        
        #convert to 2 sig figs
        H = int(H*100)
        H = H/100.
        
        return H
              
        
    #reads in the conversion constants
    def _get_constants(self):
        self.dig_T1 = self._read_ushort(0x88)
        self.dig_T2 = self._read_short(0x8A)
        self.dig_T3 = self._read_short(0x8C)
        
        self.dig_P1 = self._read_ushort(0x8E)
        self.dig_P2 = self._read_short(0x90)
        self.dig_P3 = self._read_short(0x92)
        self.dig_P4 = self._read_short(0x94)
        self.dig_P5 = self._read_short(0x96)
        self.dig_P6 = self._read_short(0x98)
        self.dig_P7 = self._read_short(0x9A)
        self.dig_P8 = self._read_short(0x9C)
        self.dig_P9 = self._read_short(0x9E)
        
        self.dig_H1 = self._read_uchar(0xA1)
        self.dig_H2 = self._read_short(0xE1)
        self.dig_H3 = self._read_uchar(0xE3)
        
        e4 = self._read_char(0xE4)
        e5 = self._read_char(0xE5)
        e6 = self._read_char(0xE6)

        self.dig_H4 = e4 << 4 | e5 & 0x0F
        self.dig_H5 = ((e5 >> 4) & 0x0F) | (e6 << 4)

        self.dig_H6 = self._read_char(0xE7)
        
    #determines how long it takes to take a reading and sleeps for this time
    def _wait_for_reading(self):
        #calculate number of samples used for each variable
        t_nsamp = 2**(self.t_oversample-1)
        p_nsamp = 2**(self.p_oversample-1)
        h_nsamp = 2**(self.h_oversample-1)
        
        #max measurement time in ms
        t = (1.25 + (2.3*t_nsamp) 
            + (2.3*p_nsamp + 0.575) 
            + (2.3*h_nsamp + 0.575))
        
        #time in seconds
        t/= 1000
        
        #sleep for this time
        time.sleep(t)
        
        

    
    #read a word (2 bytes) as an unsigned short int
    def _read_ushort(self,register):
        v = self.bus.read_word_data(self.address,register)
        return (v & 0xffff)
    
    #read a word as a signed short int
    def _read_short(self,register):
        v = self.bus.read_word_data(self.address,register)
        v&=0xffff
        if v >= 0x8000:
            v -= 0x10000
        return v
    
    #read a byte as an unsigned int
    def _read_uchar(self,register):
        v = self.bus.read_byte_data(self.address,register)
        return (v&0xff)
    
    #read a byte as a signed int
    def _read_char(self,register):
        v = self.bus.read_byte_data(self.address,register)
        v &= 0xff
        if v>0x80:
            v -= 0x100
        return v
        
        
    
if __name__ == "__main__":
    import json
    s=BME280()
    data = s.read()
    
    #prettify the output with json.dumps
    print(json.dumps(data,indent=1))
    
