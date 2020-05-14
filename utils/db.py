import pony.orm as pny
import datetime

db = pny.Database()

class Year(db.Entity):
    year = pny.PrimaryKey(int)

    months = pny.Set("Month")
    statistics = pny.Set("Yearly_statistics")

class Month(db.Entity):
    year = pny.Required(Year)
    month = pny.Required(int)

    days = pny.Set("Day")
    statistics = pny.Set("Monthly_statistics")

class Day(db.Entity):
    day = pny.Required(int)
    month = pny.Required(Month)

    statistics = pny.Set("Daily_statistics")

class Variable(db.Entity):
    name = pny.PrimaryKey(str)
    unit =  pny.Required(str)
    description = pny.Required(str)

    minval = pny.Optional(float)
    maxval = pny.Optional(float)
    cumulative = pny.Required(bool, default=False)
    
    readings = pny.Set("Reading")
    daily_statistics = pny.Set("Daily_statistics")
    monthly_statistics = pny.Set("Monthly_statistics")
    yearly_statistics = pny.Set("Yearly_statistics")
    LatestReading = pny.Set("LatestReading")


class Yearly_statistics(db.Entity):
    year = pny.Required(Year)
    variable = pny.Required(Variable)

    months=pny.Set("Monthly_statistics")

    mean = pny.Optional(float)
    minval = pny.Optional(float)
    maxval = pny.Optional(float)
    median = pny.Optional(float)
    stddev = pny.Optional(float)
    total = pny.Optional(float)
    plot = pny.Optional(str)

class Monthly_statistics(db.Entity):
    month = pny.Required(Month)
    variable = pny.Required(Variable)

    yearly_statistics = pny.Required(Yearly_statistics)

    days = pny.Set("Daily_statistics")

    mean = pny.Optional(float)
    minval = pny.Optional(float)
    maxval = pny.Optional(float)
    median = pny.Optional(float)
    stddev = pny.Optional(float)
    total = pny.Optional(float)
    plot = pny.Optional(str)

class Daily_statistics(db.Entity):
    day = pny.Required(Day)
    variable = pny.Required(Variable)

    monthly_statistics = pny.Required(Monthly_statistics)

    readings=pny.Set("Reading")
    mean = pny.Optional(float)
    minval = pny.Optional(float)
    maxval = pny.Optional(float)
    median = pny.Optional(float)
    stddev = pny.Optional(float)
    total = pny.Optional(float)
    plot = pny.Optional(str)


class Reading(db.Entity):
    date = pny.Required(datetime.datetime)
    variable = pny.Required(Variable)
    value = pny.Required(float)
    daily_statistics = pny.Required(Daily_statistics)

    metadata = pny.Optional(str)

    latest = pny.Set("LatestReading")

class LatestReading(db.Entity):
    variable = pny.PrimaryKey(Variable)
    reading = pny.Optional(Reading)
    plot = pny.Optional(str)
    mean = pny.Optional(float)
    median = pny.Optional(float)
    maxval = pny.Optional(float)
    minval = pny.Optional(float)
    stddev = pny.Optional(float)
    total = pny.Optional(float)




def initialise_database(file = "logs.sqlite"):
    db.bind('sqlite', file, create_db=True)
    db.generate_mapping(create_tables=True)










