import os
import datetime
import numpy as np

import utils.logger as logger
import utils.GetConfig as GetConfig
from .Status import command
from . import Dates



#This file contains functions that extract data from the database and prepare them for use with the website

logger.init()

homedir = os.path.expanduser("~")

#get the configuration for the logger
dbconfig = GetConfig(key="logger")

#Gets all the months with data from the logger
# returns a list of dictionaries containing:
#    text: The text we wish the month to be rendered as e.g "January 2020"
#    url: The url for this month e.g. /data/2020/01
def GetAllMonths():
    
    Months = []
    
    #get list of all the years with data
    years = logger.get_years()

    for year in years:
        #get list of all the months with data in this year
        months = logger.get_months(year)

        #construct thr dictionary for this month
        for month in months:
        
            monthnum = "%02d"%month
            monthstr = Dates.switcher[monthnum]

            text = "%s %04d"%(monthstr,year)
            #text = "%s"%(monthstr)
            url = "/data/%04d/%02d"%(year,month)

            d = {
                "text": text,
                "url": url
            }
            # print(d)
            Months.append(d)

        d={"text": "%04d"%year, "url": "/data/%04d"%year}
        Months.append(d)
    #reverse the order of the months list so the most recent month comes first
    Months.reverse()
    return Months


#Generates a structure that will be rendered as a calendar with links to days with data
# It is a list of rows, each containing 7 dictionaries corresponding to the 7 week days.
# Each day is either blank (day not in month), just the number (day with no data) or
# a hyperlink to a day with data
def CreateCalendar(year,month):

    #get the list of days in the month with data entries
    days=logger.get_days(year,month)

    #Count the number of days in a month
    # first get the first of the next month, and count the number of days
    # between then and the first of this month
    if month==12:
        nextmonth=1
        nextyear=year+1
    else:
        nextmonth=month+1
        nextyear=year
    firstofnextmonth = datetime.datetime(year=nextyear,month=nextmonth,day=1)
    firstofthismonth = datetime.datetime(year=year,month=month,day=1)
   
    daysinmonth = (firstofnextmonth-firstofthismonth).days

    #day number of first day
    d1=datetime.datetime(year=year,month=month,day=1).weekday()

    #number of rows needed
    rows = int(np.ceil(float(daysinmonth+d1)/7))

    #make calendar structure
    # This is arranged in rows with columns corresponding to M T W T F S S
    url="/data/%04d/%02d"%(year,month)
    calendar=[]
    num=1
    counter=0
    #loop over the rows
    for row in range(rows):
        week=[]
        #loop over the 7 days in a week
        for day in range(7):
            dict={}
            #If this day belongs to days in the previous or next month, leave it blank
            if (row==0 and day<d1) or (num>daysinmonth):
                dict["text"]=" "
                dict["active"]=0
                dict["url"]=""
            #fill in this day's number
            else:
                dict["text"]="%d"%num
                #If we have data, add the link to it
                if num in days:
                    dict["active"]=1
                    dict["url"]="%s/%02d"%(url,num)
                #if no data we have no link
                else:
                    dict["active"]=0
                    dict["url"]=""
                num+=1
            week.append(dict)
        calendar.append(week)
    
    return calendar

#Gets the latest data from the db
# is returned as a list of dictionaries, one per variable type
def GetLatestData():

    latest = logger.get_latest_readings()

    data = PrepData(latest)

    if data is not None:
        for reading in data:
        #create a string for the age of the data
            age = datetime.datetime.now() - reading["timestamp"]
            agestr = Dates.FuzzyTimeFromTimedelta(age)
            reading["age"] = agestr

    return data

#Gets the data for a day from the db
# is returned as a list of dictionaries, one per variable type
def GetDataForDay(year,month,day):

    data = logger.get_all_stats_for_day(year,month,day)

    return PrepData(data)

#Gets the data for a month from the db
# is returned as a list of dictionaries, one per variable type
def GetDataForMonth(year,month):

    data = logger.get_all_stats_for_month(year,month)

    return PrepData(data)

#Gets the data for a year from the db
# is returned as a list of dictionaries, one per variable type
def GetDataForYear(year):

    data = logger.get_all_stats_for_year(year)

    return PrepData(data)



#prepares the data for use with the website    
# Converts floats to strings etc
def PrepData(data):
    if data is not None:
        for reading in data:
            
            
            #Convert the floats to formatted strings
            if reading["mean"] is not None:
                reading["mean"] = "%4.1f"%reading["mean"]
                reading["median"] = "%4.1f"%reading["median"]
                reading["maxval"] = "%4.1f"%reading["maxval"]
                reading["minval"] = "%4.1f"%reading["minval"]
                reading["stddev"] = "%4.1f"%reading["stddev"]
            if reading["total"] is not None:
                reading["total"] = "%4.1f"%reading["total"]
            if "value" in reading:
                reading["value"] = "%4.1f"%reading["value"]
            
            #mangle the path for the image to something we can serve up
            if reading["plot"] is not None:
                path = os.path.relpath(reading["plot"],homedir)
                reading["plot"] = os.path.join("/files",path)
    
    return data

#gets the size of the database file (in human readable format)
def GetDBFileSize():
    file = os.path.join(dbconfig["dbdir"],dbconfig["dbname"])

    result = command(["du", "-h", "%s"%file])

    size = result.split()[0]

    return size

#returns the filename (path) of the file
def GetDBFilename():
    return os.path.join(dbconfig["dbdir"],dbconfig["dbname"])

#formats an integer in a human readable way. E.g. 1234567 -> 1,234,567
def _formatInt(i):
    #convert to a string
    s = "%d"%i

    #we want to go right to left and insert commas
    #n = Number of times we need to do this
    l=len(s)
    n = (l-1)//3
    for split in range(n):
        splitpoint = -(3*(split+1) + split)
        s = s[:splitpoint]+","+s[splitpoint:]

    return s


#gets a list of the variables held in the database. Each list element is a dict containing the variable's info
def GetDBVariables():
    vs = logger.get_variables()
    for v in vs:
        v["numreadings"] = _formatInt(v["numreadings"])

    return vs

#Gets the total number of readings in the database
def GetReadingCount():
    c = logger.get_reading_count()
    return _formatInt(c)


    


   




    
