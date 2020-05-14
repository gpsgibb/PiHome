import datetime

switcher = {
    "01": "  January",
    "02": " February",
    "03": "    March",
    "04": "    April",
    "05": "      May",
    "06": "     June",
    "07": "     July",
    "08": "   August",
    "09": "September",
    "10": "  October",
    "11": " November",
    "12": " December"
}

#From a timedelta returns a string with an approximate time
# E.g. 4 days 3 hours... = 4 days
#      5 mins 3 seconds = 5 minutes
def FuzzyTimeFromTimedelta(td):
    tds = td.total_seconds()

    days = int(tds/3600/24)
    if days == 1:
        return "%d day"%days
    elif days > 1:
        return "%d days"%days
    else:
        hours = int(tds%(3600*24)/3600)
        if hours ==1:
            return "%d hour"%hours
        elif hours > 1:
            return "%d hours"%hours
        else:
            mins = int((tds%3600)/60)
            if mins == 1:
                return "%d minute"%mins
            elif mins > 1:
                return "%d minutes"%mins
            else:
                secs = int(tds%60)
                if secs == 1:
                    return "%d second"%secs
                else:
                    return "%d seconds"%secs



#From a month number, returns a string of that month's name
def GetMonthString(year,month):
    str = "%02d"%month
    mstr = switcher[str]

    return "%s %04d"%(mstr,year)

#returns the previous and next years
def PrevNextYear(year):
    ly = "%04d"%(year-1)
    ny = "%04d"%(year+1)

    if year == datetime.date.today().year:
        return [ly,None]

    return [ly,ny]

#Return the previous and next months
def PrevNextMonth(year, month):
    ThisMonth = datetime.datetime.today().month
    ThisYear=datetime.datetime.today().year
    now=datetime.datetime.today()
    m=now.month
    y=now.year
    nm = month +1
    pm = month -1

    py=year
    ny=year

    if month == 12:
        nm = 1
        ny = year+1
    if month == 1:
        pm = 12
        py = year -1


    ps = "%04d/%02d"%(py,pm)
    ns="%04d/%02d"%(ny,nm)

    if month == int(m) and year == int(y):
        ns = None
    return [ps, ns]

#Return the previous and next days
def PrevNextDay(y,m,d):
    today = datetime.datetime(year=y, month=m, day=d, hour=23,minute=59,second=59)
    dt = datetime.timedelta(days=1)
    yesterday = today -dt
    tomorrow = today + dt

    py = yesterday.year
    pm = yesterday.month
    pd = yesterday.day

    ny = tomorrow.year
    nm = tomorrow.month
    nd = tomorrow.day

    now=datetime.datetime.now()


    ps = "%04d/%02d/%02d"%(py,pm,pd)
    if now  > today:
        ns = "%04d/%02d/%02d"%(ny,nm,nd)
    else:
        ns=None

    # print("yesterday = ",ps, "Tomorrow =", ns)
    return [ps,ns]
