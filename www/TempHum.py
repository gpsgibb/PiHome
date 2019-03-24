#!/usr/bin/env python
from __future__ import print_function
import os
import time
import datetime
import numpy as np
import Dates

home = os.path.expanduser("~")

logdir= "logs/TempHum"

dir = os.path.join(home,logdir)


#returns the last 24hrs worth of data
def get_latest_TempHum_data():
    data={}

    #get how old the "latest" data is
    file = "Temperature_Latest.png"
    fpath=os.path.join(dir,file)
    if os.path.exists(fpath):
        then=(os.path.getmtime(fpath))
        string=time_since_last_measurement(then)
        # print(string)

        data["age"]=string
    else:
        data["age"]="N/A"

    #Now get today and yesterday's date, open the log files, and get some stats for the last 24h
    today=datetime.datetime.now()
    yesterday = today + datetime.timedelta(days=-1)
    # print(today.date())
    # print(yesterday.date())

    yesterdayf = "TempHum_"+str(yesterday.date())+".log"
    f=os.path.join(dir,yesterdayf)

    t1,temp1,hum1,attempts = ReadLogFile(f)

    todayf = "TempHum_"+str(today.date())+".log"
    f=os.path.join(dir,todayf)

    t2,temp2,hum2,attempts = ReadLogFile(f)

    for i in range(len(t1)):
        t1[i]-= 86400 #subtract a day
    t=t1+t2
    temp = temp1+temp2
    hum = hum1+hum2

    if len(t) == 0:
        data["Temp"] = "N/A"
        data["MeanTemp"] = "N/A"
        data["MaxTemp"] = "N/A"
        data["MinTemp"] = "N/A"
        data["Hum"] = "N/A"
        data["MeanHum"] = "N/A"
        data["MaxHum"]= "N/A"
        data["MinHum"]= "N/A"

    else:
        latest = t[-1] #latest time
        now = datetime.datetime.now()
        midnight = datetime.datetime.combine(now.date(), datetime.time())
        seconds = (now - midnight).seconds
        # print("LATEST SECONDS", latest, seconds)
        latest=seconds
        target = latest - 3600*24 #latest time minus 1 day
        for i in range(len(t)):
            if t[i] > target: break

        # print("Cut array at i=%d"%i)
        t=t[i:]
        temp=temp[i:]
        hum=hum[i:]

        temp=np.asarray(temp)
        hum=np.asarray(hum)

        data["Temp"]="Current Temperature = %2.1f 'C"%temp[-1]
        data["MaxTemp"]="Maximum Temperature = %2.1f 'C"%temp.max()
        data["MinTemp"]="Minimum Temperature = %2.1f 'C"%temp.min()
        data["MeanTemp"]="Mean Temperature = %2.1f 'C"%temp.mean()

        data["Hum"]="Current Humidity = %2.1f %%"%hum[-1]
        data["MaxHum"]="Maximum Humidity = %2.1f %%"%hum.max()
        data["MinHum"]="Minimum Humidity = %2.1f %%"%hum.min()
        data["MeanHum"]="Mean Humidity = %2.1f %%"%hum.mean()

    return data

#Gets data for a parciular day
def get_TempHum_data(datestr):
    fname=os.path.join(dir,"TempHum_"+datestr+".log")
    if os.path.isfile(fname):
        t, temp, hum, attempts = ReadLogFile(fname)
        temp=np.asarray(temp)
        hum=np.asarray(hum)

        data={}
        data["MaxTemp"]="Maximum Temperature = %2.1f 'C"%temp.max()
        data["MinTemp"]="Minimum Temperature = %2.1f 'C"%temp.min()
        data["MeanTemp"]="Mean Temperature = %2.1f 'C"%temp.mean()

        data["MaxHum"]="Maximum Humidity = %2.1f %%"%hum.max()
        data["MinHum"]="Minimum Humidity = %2.1f %%"%hum.min()
        data["MeanHum"]="Mean Humidity = %2.1f %%"%hum.mean()
        # print(data)
        return data

    else:
        # print("%s does not exist"%fname)
        return None

#Reads in a TempHum logfile
def ReadLogFile(f):
    # print(f)
    t=[]
    temp=[]
    hum=[]
    attempts=[]
    if os.path.exists(f):
        file=open(f,"r")
        file.readline() #read header and throw it away
        for line in file:
            data=line.split()
            t.append(int(data[1]))
            temp.append(float(data[2]))
            hum.append(float(data[3]))
            attempts.append(int(data[4]))
        file.close()
        return t, temp, hum, attempts
    else:
        # print("File does not exist")
        return t, temp, hum, attempts

#Determines months for which we have data
def get_months():
    # print("Get_Months")
    # print(dir)
    files=os.listdir(dir)
    logs=[]
    #get the log files
    for file in files:
        if file.find(".log") >= 0:
            logs.append(file)

    monthDict={}
    #for each logfile, extract yyyy-mm from the name. Add this to a dictionary
    for log in logs:
        log=log.strip("TempHum_") #remove preamble
        date=log.strip(".log") #remove file extension
        date=date[:-3] #remove day
        date=date.replace("-","/")
        monthDict[date] = 0

    # print(monthDict)

    #extract sorted keys (latest first)
    months=[]
    keys = sorted(monthDict)
    keys.reverse()
    # print(keys)
    for key in keys:
        dict={}
        m=Dates.switcher[key[-2:]]
        y=key[0:4]
        dict["text"] = "%s %s"%(m,y)
        dict["url"] = os.path.join("/data",key)
        months.append(dict)
    return months

#Determines days for which we have data in a given month
def get_days(month):
    files=os.listdir(dir)
    logs=[]
    month=month.replace("/","-")
    for file in files:
        if file.find(".log") >= 0:
            logs.append(file)
    daylogs=[]
    for log in logs:
        if log.find(month) >= 0:
            daylogs.append(log)

    days=[]
    for day in daylogs:
        day=day.strip(".log")
        num=int(day[-2:])
        days.append(num)
        #print(num)

    days.sort()
    # print(days)

    return days


def time_since_last_measurement(then):
    now=time.time()
    diff=datetime.timedelta(seconds=now-then)

    str=""
    str+="The latest measurement was taken approximately "

    days=diff.days
    if days > 0:
        str+="%d day"%days
        if days > 1:
            str+="s"
    else:
        hrs = diff.seconds/3600 #hours in the day
        if hrs > 0:
            str+="%s hour"%hrs
            if hrs > 1:
                str+="s"
        else:
            mins = (diff.seconds-hrs*3600)/60 #Minutes
            if mins > 0:
                str+="%d minute"%mins
                if mins>1:
                    str+="s"
            else:
                secs = (diff.seconds - 3600*hrs - 60*mins) #seconds
                str+="%d second"%secs
                if secs !=1:
                    str+="s"
    str+=" ago"
    return(str)



if __name__ == "__main__":
    print("Latest")
    data=get_latest_TempHum_data()
    print(data)
    print("\n months")
    get_months()
    print('\n days')
    get_days("2018/10")
    print("\n data")
    get_TempHum_data("2018-09-05")
    Dates.PrevNextMonth(2019,03)
    Dates.PrevNextDay(2019,03,8)
