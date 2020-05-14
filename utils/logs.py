import pony.orm as pny
from . import db
import datetime
import random #for generating test data
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from calendar import monthrange
import json
import os

plt.switch_backend('Agg')
plotdir = "/Users/ggibb2/PiDB/plots"

def connect_logs_database(file = "logs.sqlite"):
    db.initialise_database(file)


#Registers a variable. 
# If it already exists (and matches the info given) this does nothing
# If it exists but DOES NOT match the info given, we raise an exception
@pny.db_session
def register_variable(name, unit, description, min=None, max=None, cumulative = False):
    var=db.Variable.get(name=name)
    if var is None:
        print("Variable '%s' does not exist... creating it now"%name)
        var = db.Variable(name=name, unit=unit, description=description, minval=min, maxval=max, cumulative = cumulative)
        print("Created!")
    else:
        if (var.unit != unit) or (var.description != description) or (var.minval != min) or (var.maxval != max) or (var.cumulative != cumulative):
            print("Error: Variable properties do not match what is already in the db")
            raise Exception("Trying to create a variable with properties that do not equal those already in the database")

    #we also need to create the LatestReading object for this variable    
    latest = db.LatestReading.get(variable=var)
    if latest is None:
        latest = db.LatestReading(variable=var)


#registers a reading with the database
@pny.db_session
def register_reading(variable, value, date=None, metadata="",recompute_statistics=True):
    
    #get info on the variable from the database
    Variable = db.Variable.get(name=variable)
    if Variable is None:
        raise Exception("Unknown variable %s"%variable)
    
    #unless the date is specified, we assume the reading was taken now
    if date == None:
        date = datetime.datetime.now()

    year = date.year
    month = date.month
    day = date.day
    
    #create the day in the database if it does not already exist
    # (This will also recursively create the month and year if need be)
    Day = _register_day(year,month,day)
    
    #register the daily stats table for this variable on this day (if it does not exist)
    daily_stats = _register_daily_stats(day=Day, variable=Variable)
    
    #now create the database entry for this reading
    print("Registering reading of %s = %f at %s"%(Variable.name,value,date))
    reading = db.Reading(date = date, variable=Variable, value = value, daily_statistics=daily_stats,metadata=metadata)

    #update the statistics (unless we opted not to)
    if recompute_statistics:
        generate_daily_statistics(year,month,day,variable)
        generate_monthly_statistics(year,month,variable)
        generate_yearly_statistics(year,variable)

        generate_latest_stats(variable)



#Helper to return a year object
@pny.db_session
def _get_year(year):
    return db.Year.get(year=year)

#helper to return a month object
@pny.db_session
def _get_month(year,month):
    return db.Month.get(year=year,month=month)

#helper to return a day object
@pny.db_session
def _get_day(year,month,day):
    Year = _get_year(year)
    if Year is None:
        return None
    Month = _get_month(Year, month)
    if Month is None:
        return None
    return db.Day.get(day=day, month=Month)
        
#Registers a year with the database (if it does not already exist) and returns its object
@pny.db_session
def _register_year(year):
    Year = db.Year.get(year=year)
    if Year is None:
        print("Creating year %d"%year)
        Year = db.Year(year=year)
    return Year

#Registers a month with the database (if it does not already exist) and returns its object
@pny.db_session
def _register_month(year, month):
    Year = _register_year(year)
    Month = db.Month.get(month=month, year = Year)
    if Month is None:
        print('Creating month %d-%d'%(year,month))
        Month = db.Month(month=month,year=Year)
    return Month

#Registers a day with the database (if it does not already exist) and returns its object
@pny.db_session
def _register_day(year,month, day):
    Year = _register_year(year)
    Month = _register_month(year,month)
    
    Day = db.Day.get(month=Month, day=day)
    if Day is None:
        print('Creating day %d-%d-%d'%(year,month,day))
        Day = db.Day(month=Month, day = day)
    return Day

#Registers yearly stats with the database (if it does not already exist) and returns its object
@pny.db_session
def _register_yearly_stats(year,variable):
    stats = db.Yearly_statistics.get(year=year,variable=variable)
    if stats == None:
        print("Registering yearly stats for %s for %d"%(variable.name,year.year))
        stats = db.Yearly_statistics(year=year,variable=variable)
    return stats

#Registers monthly stats with the database (if it does not already exist) and returns its object
@pny.db_session
def _register_monthly_stats(month, variable):
    monthly_stats = db.Monthly_statistics.get(month=month,variable=variable)
    if monthly_stats is None:
        yearly_stats = _register_yearly_stats(year=month.year,variable=variable)
        print("Registering monthly stats for %s for %d-%d"%(variable.name,month.year.year, month.month))
        monthly_stats=db.Monthly_statistics(month=month, variable = variable, yearly_statistics=yearly_stats)
    return monthly_stats

#Registers daily stats with the database (if it does not already exist) and returns its object
@pny.db_session
def _register_daily_stats(day,variable):
    daily_stats = db.Daily_statistics.get(day=day,variable=variable)
    if daily_stats is None:
        monthly_stats = _register_monthly_stats(day.month,variable)
        print('Registering daily stats for %s on %d-%d-%d'%(variable.name,day.month.year.year,day.month.month,day.day))
        daily_stats = db.Daily_statistics(day=day,variable=variable, monthly_statistics=monthly_stats)
    return daily_stats


#Generates statistics and plots for the last 24h of data
#This is automatically called for a variable when it has a new reaading registered
@pny.db_session
def generate_latest_stats(variable=None):

    #if no variable is passed in, recompute all variables
    if variable == None:
        variables = db.Variable.select()
    else:
        variables =db.Variable.select(lambda v: v.name == variable)

    oneDayAgo = datetime.datetime.now() - datetime.timedelta(days=1)


    for var in variables:

        Latest=db.LatestReading.get(variable=var)

        #get the latest reading and add this to the LatestReading object in the db.
        print('Getting the readings')
        r = var.readings.order_by(pny.desc(db.Reading.date)).first()
        Latest.reading = r

        #get last 24h of readings
        readings = db.Reading.select(lambda r: r.variable == var and r.date > oneDayAgo).order_by(lambda r: r.date)

        #put those readings into lists (arrays) for plotting and calculating statistics
        t=[]
        v=[]
        for r in readings:
            t.append(r.date)
            v.append(r.value)
        v=np.asarray(v)

        if len(v) > 0:
            Latest.mean = np.mean(v)
            Latest.median = np.median(v)
            Latest.maxval = np.max(v)
            Latest.minval = np.min(v)
            Latest.stddev = np.std(v)
        else:
            Latest.mean = None
            Latest.median = None
            Latest.maxval=None
            Latest.minval = None
            Latest.stddev=None
            Latest.total = None

        print("Generating latest plot for %s"%var.name)

        #plot the values over the day
        fig, ax = plt.subplots()
        myFmt = mdates.DateFormatter('%H:%M\n%d/%m')
        ax.xaxis.set_major_formatter(myFmt)
        plt.plot(t,v)
        plt.title("Latest %s"%(var.name))

        plt.ylabel("%s (%s)"%(var.name,var.unit))
        plt.ylim(var.minval,var.maxval)
        plt.xlim(oneDayAgo,datetime.datetime.now())
        
        #save the plot to file 
        fname = os.path.join(plotdir,"Latest_%s.png"%(var.name))

        plt.savefig(fname)
        plt.close()
        
        
        Latest.plot=fname



#Generates daily statistics (and a plot for that day)
#This is automatically called for a variable when it has a new reaading registered
@pny.db_session
def generate_daily_statistics(year,month,day,variable):
    print('Generating Daily statistics for %s for %d-%02d-%02d'%(variable,year,month,day))

    #get the required things from the database
    Variable = db.Variable.get(name=variable)
    Day = _get_day(year,month,day)
    stats = db.Daily_statistics.get(day=Day,variable=variable)
    
    #extract the readings for that day from the statistics
    readings = stats.readings.order_by(lambda r: r.date)

    #put the values and times of the readings into arrays
    vals = []
    t = []
    for reading in readings:
        vals.append(reading.value)
        t.append(reading.date)

    vals=np.asarray(vals)
    
    #calculate the statistics
    stats.mean = np.mean(vals)
    stats.median = np.median(vals)
    stats.minval = np.min(vals)
    stats.maxval = np.max(vals)
    stats.stddev = np.std(vals)
    
    #plot the values over the day
    fig, ax = plt.subplots()
    myFmt = mdates.DateFormatter('%H:%M')
    ax.xaxis.set_major_formatter(myFmt)
    plt.plot(t,vals)
    plt.title("%4d-%02d-%02d"%(year,month,day))
    plt.xlabel("Time")
    plt.ylabel("%s (%s)"%(Variable.name,Variable.unit))
    plt.ylim(Variable.minval,Variable.maxval)
    tmin = datetime.datetime.combine(t[0].date(),datetime.time.min)
    tmax = datetime.datetime.combine(t[0].date()+datetime.timedelta(days=1),datetime.time.min)
    plt.xlim(tmin,tmax)
    
    #save the plot to file 
    fname = os.path.join(plotdir,"Daily_%s_%04d-%02d-%02d.png"%(variable,year,month,day))
    plt.savefig(fname)
    plt.close()

    stats.plot=fname

#generates monthly statistics (and a plot for that month) 
# This is automatically called for a variable when it has a new reaading registered     
@pny.db_session
def generate_monthly_statistics(year,month,variable):
    print('Generating monthly statistics for %s for %d-%02d'%(variable,year,month))

    #get the things we need from the db
    Variable = db.Variable.get(name=variable)
    Month = _get_month(year,month)
    stats = db.Monthly_statistics.get(month=Month,variable=variable)
    
    #extract the statistics for each day in the month
    days = stats.days.order_by(lambda d: d.day.day)
    vals = []
    t = []
    minval = []
    maxval = []
    median = []
    std = []

    #create arrays of each day's statistics
    for day in days:
        vals.append(day.mean)
        t.append(day.day.day)
        minval.append(day.minval)
        maxval.append(day.maxval)
        median.append(day.median)
        std.append(day.stddev)


    vals=np.asarray(vals)
    minval = np.asarray(minval)
    maxval = np.asarray(maxval)
    median = np.asarray(median)
    std = np.asarray(std)
    
    #calculate some statistics for the month
    stats.mean = np.mean(vals)
    stats.median = np.median(vals)
    stats.minval = np.min(minval)
    stats.maxval = np.max(maxval)
    stats.stddev = np.std(vals)

    #plot the month's data
    plt.plot(t,vals,color="black")
    plt.plot(t,median,linestyle="--",color="black")
    plt.fill_between(t,minval,vals,color="blue",alpha=0.25)
    plt.fill_between(t,vals,maxval,color="red",alpha=0.25)
    plt.fill_between(t,vals-std,vals,color="blue",alpha=0.5)
    plt.fill_between(t,vals,vals+std,color="red",alpha=0.5)

    plt.title("%4d-%2d"%(year,month))
    plt.xlabel("Day")
    plt.ylabel("%s (%s)"%(Variable.name,Variable.unit))
    daysinmonth = monthrange(year,month)[1]
    plt.xlim(1,daysinmonth)
    plt.ylim(Variable.minval,Variable.maxval)
    
    #save the plot to file
    fname = os.path.join(plotdir,"Monthly_%s_%04d-%02d.png"%(variable,year,month))
    plt.savefig(fname)
    plt.close()

    stats.plot=fname
   
    
#generates yearly statistics (and a plot for that year)
#This is automatically called for a variable when it has a new reaading registered
@pny.db_session
def generate_yearly_statistics(year,variable):
    print('Generating yearly statistics for %s for %d'%(variable,year))

    #get the things we need from the db
    Variable = db.Variable.get(name=variable)
    Year = _get_year(year)
    stats = db.Yearly_statistics.get(year=Year,variable=variable)
    
    #get the monthly statistics for each month in the year
    months = stats.months.order_by(lambda n: n.month.month)

    #put them into arrays
    vals = []
    minval = []
    maxval = []
    median = []
    std = []
    t = []
    for month in months:
        vals.append(month.mean)
        t.append(month.month.month)
        minval.append(month.minval)
        maxval.append(month.maxval)
        median.append(month.median)
        std.append(month.stddev)


    vals=np.asarray(vals)
    minval = np.asarray(minval)
    maxval = np.asarray(maxval)
    median = np.asarray(median)
    std = np.asarray(std)
    
    #calculate the statistics for the year
    stats.mean = np.mean(vals)
    stats.median = np.median(vals)
    stats.minval = np.min(minval)
    stats.maxval = np.max(maxval)
    stats.stddev = np.std(vals)

    #plot he yearly statistics
    plt.plot(t,vals,color="black")
    plt.plot(t,median,linestyle="--",color="black")
    plt.fill_between(t,minval,vals,color="blue",alpha=0.25)
    plt.fill_between(t,vals,maxval,color="red",alpha=0.25)
    plt.fill_between(t,vals-std,vals,color="blue",alpha=0.5)
    plt.fill_between(t,vals,vals+std,color="red",alpha=0.5)
   
    plt.title("%4d"%year)
    plt.xlabel("Month")
    plt.ylabel("%s (%s)"%(Variable.name,Variable.unit))
    plt.xlim(1,12)
    plt.ylim(Variable.minval,Variable.maxval)
    
    #save the plot to file
    fname = os.path.join(plotdir,"Yearly_%s_%04d.png"%(variable,year))
    plt.savefig(fname)
    plt.close()

    stats.plot=fname


#(re)generate all the statistics in the db for all variables
@pny.db_session
def generate_all_statistics(yearly=True,monthly=True, daily=True):

    variables = pny.select(v for v in db.Variable)
    
    if daily:
    #generate daily statistics
        days = pny.select(d for d in db.Day)
        for day in days:
            y = day.month.year.year
            m = day.month.month
            d = day.day
            for variable in variables:
                generate_daily_statistics(y,m,d,variable.name)
    
    #generate monthly statistics
    if monthly:
        months = pny.select(m for m in db.Month)
        for month in months:
            m = month.month
            y = month.year.year
            for variable in variables:
                generate_monthly_statistics(y,m,variable.name)
    
    #generate_yearly_statistics
    if yearly:
        years = pny.select(y for y in db.Year)
        for year in years:
            y = year.year
            for variable in variables:
                generate_yearly_statistics(y,variable.name)


#Get the readings for a day, return as a list of dicts
@pny.db_session
def get_daily_readings(year,month,day,variable):
    Day = _get_day(year,month,day)

    if Day is None:
        return []

    stats = db.Daily_statistics.get(variable=variable, day=Day)

    data=[]
    for reading in stats.readings.order_by(lambda r: r.date):
        d={}
        d["timestamp"] = reading.date
        d["value"] = reading.value
        d["metadata"] = json.loads(reading.metadata)
        data.append(d)
    return data

#returns the daily statistics as a dictionary
@pny.db_session
def get_daily_stats(year,month,day,variable):
    Day = _get_day(year,month,day)

    if Day is None:
        return {}

    stats = db.Daily_statistics.get(variable=variable, day=Day)

    data = {
        "mean": stats.mean,
        "median": stats.median,
        "maxval": stats.maxval,
        "minval": stats.minval,
        "stddev": stats.stddev,
        "total": stats.total,
        "plot": stats.plot,
        "num_readings": len(stats.readings)
    }
    return data

#returns the monthly statistics as a dictionary
@pny.db_session
def get_monthly_stats(year,month,variable):
    Month = _get_month(year,month)

    if Month is None:
        return {}

    stats = db.Monthly_statistics.get(variable=variable, month=Month)

    data = {
        "mean": stats.mean,
        "median": stats.median,
        "maxval": stats.maxval,
        "minval": stats.minval,
        "stddev": stats.stddev,
        "total": stats.total,
        "plot": stats.plot,
    }
    return data

#returns the yearly statistics as a dictionary
@pny.db_session
def get_yearly_stats(year,variable):
    Year = _get_year(year)

    if Year is None:
        return {}

    stats = db.Yearly_statistics.get(variable=variable, year=Year)

    data = {
        "mean": stats.mean,
        "median": stats.median,
        "maxval": stats.maxval,
        "minval": stats.minval,
        "stddev": stats.stddev,
        "total": stats.total,
        "plot": stats.plot,
    }
    return data

#returns the latest readings as a list of dictionaries
@pny.db_session
def get_latest_readings():
    readings = db.LatestReading.select().order_by(lambda r: r.variable)

    if len(readings) == 0:
        return None

    data=[]
    for reading in readings:
        if reading.reading is not None:
            d = {
                "variable": reading.variable.name,
                "value": reading.reading.value,
                "timestamp": reading.reading.date,
                "unit": reading.variable.unit,
                "mean": reading.mean,
                "median": reading.median,
                "minval": reading.minval,
                "maxval": reading.maxval,
                "stddev": reading.stddev,
                "total": reading.total,
                "plot": reading.plot
            }
            data.append(d)
    return data

@pny.db_session
def get_all_stats_for_day(year,month,day):
    Day = _get_day(year,month,day)

    if Day is None:
        return None

    Stats = Day.statistics.order_by(lambda s: s.variable)
    
    daily = []
    for stat in Stats:
        d = {
                "variable": stat.variable.name,
                "unit": stat.variable.unit,
                "mean": stat.mean,
                "median": stat.median,
                "minval": stat.minval,
                "maxval": stat.maxval,
                "stddev": stat.stddev,
                "total": stat.total,
                "plot": stat.plot
            }
        daily.append(d)
    
    return daily

@pny.db_session
def get_all_stats_for_month(year,month):
    Month = _get_month(year,month)

    if Month is None:
        return None
    
    Stats = Month.statistics.order_by(lambda s: s.variable)

    Monthly = []
    for stat in Stats:
        d = {
                "variable": stat.variable.name,
                "unit": stat.variable.unit,
                "mean": stat.mean,
                "median": stat.median,
                "minval": stat.minval,
                "maxval": stat.maxval,
                "stddev": stat.stddev,
                "total": stat.total,
                "plot": stat.plot
            }
        Monthly.append(d)
    
    return Monthly

@pny.db_session
def get_all_stats_for_year(year):
    Year = _get_year(year)

    if Year is None:
        return None
    
    Stats = Year.statistics.order_by(lambda s: s.variable)

    Yearly = []
    for stat in Stats:
        d = {
                "variable": stat.variable.name,
                "unit": stat.variable.unit,
                "mean": stat.mean,
                "median": stat.median,
                "minval": stat.minval,
                "maxval": stat.maxval,
                "stddev": stat.stddev,
                "total": stat.total,
                "plot": stat.plot
            }
        Yearly.append(d)
    
    return Yearly

#returns a list of the years in the database (as integers, e.g. [2019,2020])
@pny.db_session
def get_years():
    Y = db.Year.select().order_by(db.Year.year)
    years=[]
    
    if Y is not None:
        for y in Y:
            years.append(y.year)
    return years

#returns a list of the months available in the specified year as integers (e.g. [1,2,3,4,11,12])
@pny.db_session
def get_months(year):
    y = _get_year(year)
    if y is None:
        return []

    Months = y.months.order_by(db.Month.month)

    months = []

    for month in Months:
        months.append(month.month)

    return months

#returns a list of the days belonging to the speficied month as integers (e.g. [1,2,3,4,29,30])
@pny.db_session
def get_days(year,month):
    m = _get_month(year,month)

    if m is None:
        return []
    
    Days = m.days.order_by(db.Day.day)
    
    days=[]

    for day in Days:
        days.append(day.day)

    return days



if __name__ == "__main__":

    connect_logs_database("testdb.sqlite")

    register_variable("testVar","bananas", "a test variable",min=0.,max=1.)

    #register_reading("testVar",random.random())
    register_reading("testVar",random.random(),date=datetime.datetime.now()-datetime.timedelta(days=2))
    register_reading("testVar",random.random(),date=datetime.datetime.now()-datetime.timedelta(days=5))


    print(get_latest_readings())


    print(get_years())
    print(get_months(2020))
    print(get_days(2020,5))


    # today = datetime.date.today()



    
    # # #generate random data once an hour for a year
    # tstart = datetime.datetime(year = 2000, month=1, day = 1, hour=0, minute=0,second=0)
    # dt = datetime.timedelta(minutes=60)
    # tstop =  datetime.datetime(year = 2001, month=1, day = 1, hour=0, minute=0,second=0)
    
    # t=tstart
    # while t < tstop:
    #     omega = (t-tstart).total_seconds()/3600/24
    #     register_reading(variable="testVar", value=random.gauss(np.sin(omega)+2*np.sin(omega/30),np.abs(np.sin(omega/7))),date = t,recompute_statistics=False)
    #     t+=dt


    # # #generate statistics
    # generate_all_statistics()
   

    # print(get_latest_readings())
