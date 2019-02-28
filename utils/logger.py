#!/usr/bin/env python
from __future__ import print_function
import numpy as np
import os
import sys
import datetime
import time
import matplotlib.pyplot as plt
import matplotlib.dates as dates

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
            print("Logger: Making root log directory: '%s'"%logdir)
            os.mkdir(logdir)
            
        self.dir = logdir+"/"+self.name
        
        #see if directory for this particular log name exists, if not, create it
        if not os.path.isdir(self.dir):
            print("Logger: Making %s log directory: '%s'"%(self.name,self.dir))
            os.mkdir(self.dir)
        
        #define today's date
        self.today = str(datetime.date.today())
        
        self.logfile=None
        
        self.cachedata()
        
        #open logfile for writing
        self.openLog()
        
        self.lasttime=time.time()
    
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
            #make a daily summary plot
            self.prune_old_values()
            self.plot(title=self.today)
            
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
        
        #append data to historical cache
        #first offset the historical 'time since latest measurement' by our new measurement time
        dt = time.time() - self.lasttime
        self.lastime = time.time()
        for i in range(len(self.historical["seconds"])):
            self.historical["seconds"][i] -= dt
        #now add our new data
        self.historical["seconds"].append(0)
        for name in self.names:
            self.historical[name].append(args.get(name))
        #now prune old data
        self.prune_old_values()
        
        #finally plot the new summary
        self.plot("Latest")
            
        self.lasttime=time.time()
        
                
        
    
    # store the last 24h of data for logging purposes    
    # This is called once during init to read in any existing log files
    # afterwards this cache is updated each time a measurement is logged
    # in the self.log() method
    def cachedata(self):
        #get today's date and yesterday's date
        today=datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)
        
        #get filenames for today and yesterday
        yesterdayfile = self.dir+"/"+self.name+"_"+str(yesterday)+".log"
        todayfile = self.dir+"/"+self.name+"_"+str(today)+".log"
        
        #create dictionary to store the data in
        self.historical = {}
        self.historical["seconds"] = []
        self.historical["time"] = []
        for name in self.names:
            self.historical[name] = []
        
        day = 3600*24
        
        #see if yesterday's file exists - if so, read it
        print(yesterdayfile)
        if os.path.isfile(yesterdayfile):
            f=open(yesterdayfile,"r")
            for line in f:
                if line[0] == "#": continue
                data=line.split()
                t = int(data[1])-day
                self.historical["seconds"].append(t)
                i=2
                for name in self.names:
                    try:
                        val = float(data[i])
                    except:
                        val = 0
                    self.historical[name].append(val)
                    i+=1
            f.close()
        #see if today's file exists - if so, read it
        print(todayfile)
        if os.path.isfile(todayfile):
            f=open(todayfile,"r")
            for line in f:
                if line[0] == "#": continue
                data=line.split()
                t = int(data[1])
                self.historical["seconds"].append(t)
                i=2
                for name in self.names:
                    try:
                        val = float(data[i])
                    except:
                        val = 0
                    self.historical[name].append(val)
                    i+=1
            f.close()
        
        #determine current time from midnight in seconds
        seconds=self.get_seconds_from_midnight()
        
        #store the time we define as zero in our historical log (i.e. now)
        self.lasttime=time.time()
        
        #subtract from the array of seconds to get time before now
        
        for i in range(len(self.historical["seconds"])):
            self.historical["seconds"][i] -= seconds
        
        #remove values older than a day
        self.prune_old_values()
        
        
        if (len(self.historical["seconds"]) > 0): self.plot("Latest")
        
        
        
    def prune_old_values(self):
        #seconds in a day
        day = 3600*24
        
        if (len(self.historical["seconds"]) == 0): return
        #prune off the values older than a day
        while True:
            if self.historical["seconds"][0] < -day:
                self.historical["seconds"].pop(0)
                for name in self.names:
                    self.historical[name].pop(0)
            else:
                break
        
    def get_seconds_from_midnight(self):
        t=datetime.datetime.now()
        hh=t.hour
        mm=t.minute
        ss=t.second
        seconds = hh*3600 + mm*60 +ss
        return seconds
    
    #make plots of the last 24h of data    
    def plot(self,title):
        now=datetime.datetime.now()
        t=[]
        for tm in self.historical["seconds"]:
            t.append(now + datetime.timedelta(seconds=tm))
        
        t=np.asarray(t)
        
        fmt=dates.DateFormatter("%H:%M\n %d/%m")

        
        for name in self.names:
            v=[]
            for x in self.historical[name]:
                v.append(x)
            v=np.asarray(v)
            fig, ax = plt.subplots()
            plt.plot(t,v)
            plt.title(title)
            plt.ylabel(name)
            ax.xaxis.set_major_formatter(fmt)
            plt.savefig(self.dir+"/"+name+"_"+title+".png")
            plt.close()
            fig.clf()
            ax.cla()
        
    
    def finalise(self):
        print("Logger: Finalising")
        self.logfile.close()
        
        
    
        
    
                
                 
if __name__ == "__main__":
        
    log=Logger("TempHum",3,["Temperature","Humidity", "attempts"])
    
        
        
        
        
        
        
        
        
