from __future__ import print_function
import numpy as np
import matplotlib.pyplot as plt
from drivers import ADS1115
import time
import datetime
import utils.logger as logger


# Wiring
# 3v3 ---------------------------------------------------------
#           |               ________________________
#           |               |           |     ______|______
#          | |              |   burden | |   |             |
#          | | 10k          |          | |   | Transformer |
#           |             -----         |    |_____________|
#           |            |     |        |___________|
#           -------------| ADC |             |
#           |         |  |     |             |
#           |         |   -----              |
#          | |        |______________________|
#          | | 10k
#           |
#           |
# GND ---------------------------------------------------------


#burden resistor (Ohms)
R=20

#Peak wall current for the sensor (Amps)
Amax = 100

#induced current at Amax (mA)
mAmax = 50

#number of voltage measurements to take
N = 500

#Frequency of the AC (Hz)
freq = 50

# RMS voltage of the mains electricity (V)
V_RMS = 230

##Various derived constants

#Angular frequency
omega = 2 * np.pi*50 #2*pi*f
#converts voltage to current in the transformer coil
# I = V/R: 1V = 1/R A
V2mA = 1./R 
# converts current in the tranformer to current in the wall 
mA2A = Amax/mAmax*1000


# returns the resolution of the ADC (in W)
def get_error(adc):
    dV=adc.get_resolution()
    dmA = dV*V2mA
    dA = dmA*mA2A
    dP = dA*V_RMS
    return dP

# Returns the maximum power that can be measured
def get_max_power(adc):
    vmax = adc.get_vmax()
    #vmax = 3.3/2
    mAmax = V2mA*vmax
    Amax = mA2A*mAmax
    Pmax = Amax*V_RMS
    return Pmax

#Reads the voltage across the curent transformer N times
def take_readings(adc):
    
    #tell the ADC to use A0 and A1 inputs
    adc.set_input(0)
    #tell ADC to take highest temporal resolution of data points
    adc.set_rate(7)
    
    vs = np.zeros(N)
    ts = np.zeros(N)
    
    adc.set_mode(1)
    
    t0 = time.time()
    
    for i in range(N):
        for attempt in range(10):
            val = adc.read()
            if val is not None:
                vs[i]= val
                ts[i] = time.time()-t0
                break
            if attempt == 9:
                raise ValueError("Cannot get a reading from the ADC")
    
    return ts, vs



# Calculate the power from the voltage readings
def get_power(t,v):
    
    # fit V(t) = V0 + S*sin(omega*t) + C*cos(omega*t)
    s = np.sin(omega*t)
    c = np.cos(omega*t)
    
    S0=0.
    C0=0.
    V0=0.
    
    #iterate 5 times
    for i in range(5):
        V0 = np.sum(v - S0*s - C0*c)/len(t)
        S0 = np.sum((v - V0 - C0*c)*s)/np.sum(s*s)
        C0 = np.sum((v - V0 - S0*s)*c)/np.sum(c*c)
        #print("Iteration %d: V0=%f, C0=%f. S0=%f"%(i,V0,C0,S0))
    
    A0 = np.sqrt(C0*C0 + S0*S0)
    #print("Sinusoidal amplitude = %fV"%A0)
    #print("RMS Sinusoidal amplitude = %fV"%(A0/np.sqrt(2)))
        
    
    #Better (?) method is to just calculate the RMS value firectly from the data
    
    A = (np.max(v) - np.min(v))/2.
    #print("Signal amplitude = %fV"%A)
    rms = np.sqrt(np.sum(v*v)/len(v))
    #print("RMS signal = %fV"%rms)
   
    mA = rms*V2mA
    A = mA*mA2A
    #print("Current (RMS) in transformer = %fmA"%(mA*1000))
    #print("Current (RMS) in wire = %fA"%(A))
    P = A*V_RMS
    
    return P
    

if __name__ == "__main__":
    adc = ADS1115()
    #dP = get_error(adc)
    #Pmax = get_max_power(adc)
    
    logger.init()
    logger.register_variable("Power","Watts","Power consumption",min=0)
    logger.register_variable("Energy","kWh","Energy consumed",min=0,cumulative=True)
    
    #main loop for taking measurements
    t0=time.time()
    while True:
        p = 0
        ttot = 0
        #take 10 power measurements, and log the time-averaged power and energy over these measurements
        for i in range(10):
            t,v, = take_readings(adc)
            P = get_power(t,v)
            
            timestamp = datetime.datetime.now()
            t1=time.time()
            print("%s: %d W"%(timestamp,P))
            
            p += P*(t1-t0)
            ttot += (t1-t0)
            
            time.sleep(5)
            t0=t1
            
        pavg = p/ttot
        print("Average power = %dW"%pavg)
        kWh = pavg*ttot/3600/1000
        print("Energy = %fkWh"%kWh)
        
        logger.register_reading(variable="Power",value=pavg)
        logger.register_reading(variable="Energy",value=kWh)
        
