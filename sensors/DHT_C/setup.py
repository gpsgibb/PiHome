from distutils.core import setup, Extension

setup(name="DHTC", version="0.1", ext_modules=[Extension("DHTC",["DHT.c"],libraries=["wiringPi"])])

