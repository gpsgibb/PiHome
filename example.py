from __future__ import print_function
import sensors
import drivers

adc=drivers.PCF8591()
adc.set_input_mode(0)
adc.set_input_channel(0)
T=sensors.Thermistor(adc)

print("Temperature = %f 'C"%T.read()) 


dht=sensors.DHT(pin=21,sensortype=22)
result=dht.read()

if result["status"] == sensors.DHTsensor.SUCCESS:
    print( result["Temperature"],result["Humidity"])
else:
    print("Error, could not successfully read from DHT")

dht.finalise()
adc.finalise()
