import os
import datetime
import numpy as np

import utils.logs as logs
from . import Dates

#This file contains functions that extract data from the database and prepare them for use with the website

logs.connect_logs_database()

homedir = os.path.expanduser("~")

#Gets all the months with data from the logs
# returns a list of dictionaries containing:
#    text: The text we wish the month to be rendered as e.g "January 2020"
#    url: The url for this month e.g. /data/2020/01
def GetAllMonths():
    
    Months = []
    
    #get list of all the years with data
    years = logs.get_years()

    for year in years:
        #get list of all the months with data in this year
        months = logs.get_months(year)

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
    days=logs.get_days(year,month)

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

    latest = logs.get_latest_readings()

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

    data = logs.get_all_stats_for_day(year,month,day)

    return PrepData(data)

#Gets the data for a month from the db
# is returned as a list of dictionaries, one per variable type
def GetDataForMonth(year,month):

    data = logs.get_all_stats_for_month(year,month)

    return PrepData(data)

#Gets the data for a year from the db
# is returned as a list of dictionaries, one per variable type
def GetDataForYear(year):

    data = logs.get_all_stats_for_year(year)

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
            
            #mangle the path for the image to something we can serve up
            if reading["plot"] is not None:
                path = os.path.relpath(reading["plot"],homedir)
                reading["plot"] = os.path.join("/files",path)
    
    return data
    


   




    