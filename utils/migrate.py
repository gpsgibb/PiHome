import logger
import datetime
import json
import os

#extracts the date from a filename and turns it into a datetime object (at 00:00:00)
def date_from_filename(fname):
    datestr = fname.split("_")[-1].split(".")[0]
    print("%s"%datestr)
    return datetime.datetime.strptime(datestr,"%Y-%m-%d")

#Reads in a TempHum logfile and if its contents are not already in the db, puts them in it
def read_TempHum_file(file):

    day = date_from_filename(file)

    f=open(file,"r")
    lines = f.readlines()
    f.close()

    header = lines.pop(0)
    
    #get number of readings in log file
    numreadings = len(lines)
    
    #get readings in the database for this day and count them
    dbreadings = logger.get_daily_readings(day.year,day.month,day.day,"Temperature")
    numdb = len(dbreadings)
    
    #data in database seems to match data in logfile. Skip this file
    if numdb == numreadings:
        print("All data present in database for this day. Skipping")
        return
   
    #loop through lines in file, and add readings if they are not already in the database
    i=0
    for line in lines:
        #for i<numdb, the readings are already in the db. Skip
        if i<numdb:
            i+=1
            continue

        data = line.split()
        time = data[0]
        seconds = int(data[1])
        temperature = float(data[2])
        humidity = float(data[3])
        attempts = int(data[4])

        dt = datetime.timedelta(seconds=seconds)
        
        print(day+dt, temperature, humidity)
        
        #put the attempts in as metadata (in json format)
        metadata = json.dumps({"attempts":attempts})

        #register the data, opting to not recompute the statistics as we will do this at the end of the day
        logger.register_reading(variable="Temperature",
                                value = temperature, 
                                date=day+dt,
                                metadata = metadata,
                                recompute_statistics=False)
        logger.register_reading(variable="Humidity",
                                value = humidity, 
                                date=day+dt,
                                metadata = metadata,
                                recompute_statistics=False)
    
    #update/generate the statistics for this day
    logger.generate_daily_statistics(day.year,day.month,day.day,"Temperature")
    logger.generate_daily_statistics(day.year,day.month,day.day,"Humidity")

    




if __name__ == "__main__":
    logger.connect_logger_database()

    #register temperature and humidity with the database
    logger.register_variable(name="Temperature",
                           unit="°C",
                           description="Bedroom Temperature",
                           min=15.0,
                           max=30.0)
    logger.register_variable(name="Humidity",
                           unit="%",
                           description="Bedroom Relative Humidity",
                           min=0.0,
                           max=100.0)
    
    #get all the log files and read them into the database
    logfiles = os.listdir("logger")
    logfiles.sort()
    for logfile in logfiles:
        read_TempHum_file("logger/%s"%logfile)
    
    #finally compute all the statistics
    logger.generate_all_statistics(yearly=True,monthly=True,daily=False)

    logger.generate_latest_stats()




    
