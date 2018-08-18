#!/usr/bin/env python
from __future__ import print_function
import numpy as np
import time
import math

# Class to get temerature from a thermistor

# Default constant values 
# (can be modified by passing different values to the class constructor)
C2K = 273.15 #celsius to kelvin
R0 = 10. #thermistor's reference resistance
B=3950. #thermistor's B parameter
T0=25.+C2K #Thermistor's reference temperature (in K)
Rref = 10. #resistance of reference resistor (default 10K)
Vmax = 255. #maximum adc value of resistance

# Wiring instructions:
# -----------------------------3v3
#    |
#   [ ] Rref
#    |
#    |------------------
#    |                 |
#   [\] Thermistor    ADC   
#    |                 |
#------------------------------GND

class Thermistor:
    def __init__(self,adc,R0=R0, B=B, T0=T0, Rref=Rref, Vmax=Vmax):
        print("Thermistor: Initialised")
        self.adc=adc
        self.R0=R0
        self.B=B
        self.T0=T0
        self.Rref=Rref
        self.Vmax=Vmax
    
    # Returns the temperature in degrees C
    def read(self):
        V=self.adc.read()
        R=self.__get_R(V)
        T=self.__get_T(R)
        return T
        
    #returns the resolution of the sensor around a temperature       
    def get_resolution(self,T):
        #get the resistance of the thermistor
        R = self.R0 * np.exp(self.B *( 1./(T+C2K) - 1./(self.T0)))
        # ratio of resistances
        K = R/self.R0
        #solve for the voltage across the thermistor (in ADC units)
        V = self.Vmax * K / (1+K)
        #get the closest measureable voltage to the temperature, and those above and below it
        Vref = int(V)
        Vdown = Vref-1
        Vup = Vref+1
        # determine the maximum and minimum temperature that could be reported
        Tmax = self.__get_T(self.__get_R(Vdown))
        Tmin = self.__get_T(self.__get_R(Vup))
        #calculate error
        dT = (Tmax-Tmin)/2
        
        return dT
    
    # Returns resistance of the thermistor in KOhm (private to class)
    def __get_R(self,Vin):
        if Vin == Vmax:
            R=float("inf")
        else:
            R = self.Rref * (Vin/(self.Vmax-Vin))
        return R
        
    # Returns the Temperature in degrees C (private to class)
    def __get_T(self,R):
        # T = 1/ (1/B ln(R/R0) + 1/T0)
        if R == 0:
            T = float("inf")
            return T
        elif R == float("inf"):
            T=0.-C2K
            return T
        else:
            T = 1./self.B*np.log(R/self.R0)+ 1./self.T0
            return 1/T-C2K
            
    

        
#Test/example code. Read in 3 different thermistors and display their temperatures
    
if __name__ == "__main__":
    import PCF8591
    #import DHT
    try:
        adc=PCF8591.PCF8591()
        adc.set_input_mode(0)
        thermistor=Thermistor(adc)
        #DHT22=DHT.DHT(21,sensortype=22)
        print("")
        
        adc.set_input_channel(0)
        T=thermistor.read()
        print("Temperature= %f 'C"%T)
        
        print("")
        adc.set_input_channel(1)
        T=thermistor.read()
        print("Temperature= %f 'C"%T)
        
        print("")
        adc.set_input_channel(2)
        T=thermistor.read()
        print("Temperature= %f 'C"%T)
        
        for i in range(-10,40):
            dT=thermistor.get_resolution(i)
            print(i, dT)
            
            
        
        #~ print("")
        #~ print("Reading DHT:")
        #~ result = DHT22.read()
        #~ if result["status"] == DHT.SUCCESS:
            #~ temp=result["Temperature"]
            #~ hum=result["Humidity"]
            #~ AT = temp +0.33*(hum/100. *6.105*np.exp(17.27*temp/(237.7+temp)))-4
            #~ print("Temp= %2.1f 'C, Humidity=%2.1f%%, Apparent Temperature = %2.1f 'C"%(temp,hum,AT))
        #~ print("")
        #~ DHT22.finalise()
            
        
    finally:
        print("")
        adc.finalise()
    
