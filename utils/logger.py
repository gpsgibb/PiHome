#!/usr/bin/env python
from __future__ import print_function
import numpy as np
import os
import sys
import datetime
import time

logdir = "/home/pi/logs"

# Class for logging measurements
# measurements are written to log files, with a new file each day

class Logger:
    def __init__(self,name,numargs,names):
        self.name=name
        self.numargs=numargs
        self.names=names
        
        # check for consistency with number of arguments and names
        if len(names) != numargs:
            print("Logger ERROR: number of argument names does not match number of arguments")
            sys.exit()
            
        #check that main log directory exists. If not, make it
        if not os.path.isdir(logdir):
            print("Logger: Making root log directory: '%s'")
            os.mkdir(logdir)
            
        self.dir = logdir+"/"+self.name
        
        #see if directory for this particular log name exists, if not, create it
        if not os.path.isdir(self.dir):
            print("Logger: Making %s log directory: '%s'"%(self.name,self.dir))
            os.mkdir(self.dir)
        
        #define today's date
        self.today = str(datetime.date.today())
        
        self.logfile=None
        
        #open logfile for writing
        self.openLog()
    
    #opens a logfile for writing to
    def openLog(self):
        fname=self.dir+"/"+self.name+"_"+self.today+".log"
        
        #check if this logfile is new. If so, write a header to it
        newfile = not os.path.isfile(fname)
        if newfile:
            print("Logger: opening new logfile '%s'"%fname)
        else:
            print("Logger: opening existing logfile '%s'"%fname)
        
        self.logfile = open(fname,"a")
        if newfile:
            self.logfile.write("# Time, seconds")
            for name in self.names:
                self.logfile.write(", "+name)
            self.logfile.write("\n")
    
    #write a log to the logfile. 
    def log(self,**args):
        #check that it's still 'today'. If not, make new logfile
        date = str(datetime.date.today())
        if date != self.today:
            print("Logger: New day, new logfile")
            self.today=date
            self.logfile.close()
            self.openLog()
        
        #get the current time in both hh:mm:ss format and seconds after midnight
        t=datetime.datetime.now()
        hh=t.hour
        mm=t.minute
        ss=t.second
        seconds = hh*3600 + mm*60 +ss
        
        timestr = str("%02d:%02d:%02d"%(hh,mm,ss))
        
        self.logfile.write(timestr+" "+"%5d"%(seconds)+" ")
        #loop over all the supplied data values and write them
        for name in self.names:
            self.logfile.write(" "+str(args.get(name)))
        
        self.logfile.write("\n")
        self.logfile.flush()
    
    def finalise(self):
        print("Logger: Finalising")
        self.logfile.close()
        
        
    
        
    
                
                 
if __name__ == "__main__":
        
    log=Logger("testlog",2,["a","b"])
    
    for i in range(10):
        a=np.random.random()
        b=np.random.random()
        log.log(a=a,b=b)
        time.sleep(1)
        
        
        
        
        
        
        
        
