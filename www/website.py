#!/usr/bin/env python
import flask
import os
from TempHum import get_latest_TempHum_data, get_days, get_TempHum_data, get_months
import datetime
import Status
import Directories
import Dates
import numpy as np

app = flask.Flask(__name__)

rootdir = os.path.expanduser("~")

hostname=Status.command("hostname")


#Welcome page
@app.route("/")
def WelcomePage():
    return(flask.render_template("index.html",hostname=hostname))

#Shows the status of the machine
@app.route("/status")
def StatusPage():
    data={}

    result = Status.command(["df","-h"])
    data["Disk Info"]=result

    result=  Status.command("uptime")
    data["Uptime"]=result

    result=Status.command("ifconfig")
    data["Network"] = result

    return flask.render_template("status.html",data=data,hostname=hostname)

#Filesystem browser. Browses all files in $HOME
@app.route("/files/")
@app.route("/files/<path:file>")
def FileServerPages(file=""):
    path=os.path.join(rootdir,file)
    parent=os.path.join("/files",os.path.dirname(file))

    # print("File Path = '%s'"%path)
    # print("Parent URL = '%s'"%parent)
    if os.path.isdir(path):
        parents = Directories.get_parent_dirs(file)
        content=Directories.list_directory(path,os.path.join("/files",file))
        return flask.render_template("directory.html",content=content, dir=path,parents=parents,hostname=hostname)

    else:
        return flask.send_file(path)

#Entry page to the data pages. Shows the latest data
@app.route("/data")
@app.route("/data/")
def LatestDataPage():
    datadir = "logs/TempHum"
    dir = os.path.join(rootdir,datadir)

    data = get_latest_TempHum_data()

    months=get_months()

    today=datetime.datetime.today()
    year=today.year
    month=today.month
    day = today.day

    data["TempImg"]="%s"%os.path.join("/files",datadir,"Temperature_Latest.png")
    data["HumImg"]="%s"%os.path.join("/files",datadir,"Humidity_Latest.png")
    data["AttemptImg"]="%s"%os.path.join("/files",datadir,"Attempts_Latest.png")

    response=flask.make_response(flask.render_template("data.html",hostname=hostname,data=data, months=months,DataTitle="Latest Data",PrevNext=Dates.PrevNextDay(year, month,day)))

    return request_no_caching(response)


#Displays a calendar for the month, allowing the user to select a day
@app.route("/data/<int:year>/<int:month>")
def MonthViewPage(year,month):
    if year > datetime.datetime.now().year or year<2018:
        return("invalid date")
    if month<1 or  month>12:
        return("invalid date")
    string="%04d/%02d"%(year,month)
    # print("Month = %s"%string)
    days=get_days(string)

    #days in month
    if month==12:
        nextmonth=1
        nextyear=year+1
    else:
        nextmonth=month+1
        nextyear=year
    daysinmonth = datetime.datetime(year=nextyear,month=nextmonth,day=1)-datetime.datetime(year=year,month=month,day=1)
    daysinmonth = daysinmonth.days

    #day number of first day
    d1=datetime.datetime(year=year,month=month,day=1).weekday()
    # print("Weekday=",d1)
    # print("days in month=",daysinmonth)

    #number of rows needed
    rows = int(np.ceil(float(daysinmonth+d1)/7))
    # print("Number of rows =",rows)

    #make calendar structure
    url="/data/%04d/%02d"%(year,month)
    calendar=[]
    num=1
    counter=0
    for row in range(rows):
        week=[]
        for day in range(7):
            dict={}
            if (row==0 and day<d1) or (num>daysinmonth):
                dict["text"]=" "
                dict["active"]="0"
                dict["url"]=""
            else:
                dict["text"]="%d"%num
                if num in days:
                    dict["active"]=1
                    dict["url"]="%s/%02d"%(url,num)
                else:
                    dict["active"]=0
                    dict["url"]=""
                num+=1
            week.append(dict)
        calendar.append(week)
    # print(["Mon","Tue","Wed","Thu","Fri","Sat","Sun"])
    # for week in calendar:
        # for day in week:
            # print(day["text"],day["active"],day["url"])

    months=get_months()
    title="No Data"

    title=Dates.GetMonthString(year,month)


    return flask.render_template("data.html",months=months,hostname=hostname,calendar=calendar,DataTitle=title,PrevNext=Dates.PrevNextMonth(year, month))


# Shows data for a particular day
@app.route("/data/<int:year>/<int:month>/<int:day>")
def DataForDayPage(year,month,day):
    # print(year,month, day)
    datestring="%04d-%02d-%02d"%(year,month,day)
    data = get_TempHum_data(datestring)

    if datetime.date.today() == datetime.date(year=year,month=month,day=day):
        return flask.redirect("/data")

    if data == None:
        title = datestring
        months=get_months()
        return flask.render_template("data.html",hostname=hostname,months=months,DataTitle=title,PrevNext=Dates.PrevNextDay(year, month,day))

    tempfile="Temperature_%s.png"%datestring
    humfile="Humidity_%s.png"%datestring
    atfile="Attempts_%s.png"%datestring

    datadir = "logs/TempHum"
    data["TempImg"]="%s"%os.path.join("/files",datadir,tempfile)
    data["HumImg"]="%s"%os.path.join("/files",datadir,humfile)
    data["AttemptImg"]="%s"%os.path.join("/files",datadir,atfile)

    months=get_months()

    return flask.render_template("data.html",data=data,hostname=hostname,months=months,DataTitle=datestring,PrevNext=Dates.PrevNextDay(year, month,day))


#Request that we don't cache anything
def request_no_caching(response):
    response.headers["Cache-Control"]='no-cache, no-store, must-revalidate'
    response.headers["pragma"]='no-cache'
    response.headers["expires"]="0"
    return response



if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
