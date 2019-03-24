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


#From a month number, returns a string of that month's name
def GetMonthString(year,month):
    str = "%02d"%month
    mstr = switcher[str]

    return "%s %04d"%(mstr,year)

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
    # print("Previous month =", ps, " next month= ",ns)
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
