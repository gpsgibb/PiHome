#!/usr/bin/env python
import flask
import os
import datetime
import numpy as np
import json

from . import Status, FromLogs, Directories, Dates


app = flask.Flask(__name__)

homedir = os.path.expanduser("~")
hostname=Status.command("hostname")

#Welcome page
@app.route("/")
def WelcomePage():
    return(flask.render_template("index.html",hostname=hostname))

#Shows the status of the machine
# (runs some commands and returns their output)
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
    path=os.path.join(homedir,file)
    parent=os.path.join("/files",os.path.dirname(file))

    #If it's a directory we display its contents
    if os.path.isdir(path):
        parents = Directories.get_parent_dirs(file)
        content=Directories.list_directory(path,os.path.join("/files",file))
        return flask.render_template("directory.html",content=content, dir=path,parents=parents,hostname=hostname)

    #otherwise we send the file
    else:
        return flask.send_file(path)



#Entry page to the data pages. Shows the latest data
@app.route("/data")
@app.route("/data/")
def LatestDataPage():

    #get the list of months which we put in the LHS of the page as quick links
    months = FromLogs.GetAllMonths()
    
    #get the latest data from the database
    data = FromLogs.GetLatestData()
        
    #Work out what the previous and next days are - This is displayed at the top
    #of the page as quick links
    today=datetime.datetime.today()
    year=today.year
    month=today.month
    day = today.day
    PrevNext=Dates.PrevNextDay(year, month,day)

    response=flask.make_response(flask.render_template("data.html",hostname=hostname,data=data, months=months,DataTitle="Latest Data",PrevNext=PrevNext))

    return request_no_caching(response)


# Shows summary for a particular year
@app.route("/data/<int:year>")
def DataForYearPage(year):

    data = FromLogs.GetDataForYear(year)

    months=FromLogs.GetAllMonths()

    PrevNext=Dates.PrevNextYear(year)

    pagetitle="%04d"%(year)

    return flask.render_template("data.html",data=data,hostname=hostname,months=months,DataTitle=pagetitle,PrevNext=PrevNext)



#Displays a calendar for the month, allowing the user to select a day
@app.route("/data/<int:year>/<int:month>")
def DataForMonthPage(year,month):

    months=FromLogs.GetAllMonths()

    if month<1 or month>12:
        return flask.render_template("data.html",months=months,hostname=hostname,DataTitle="Invalid Month",PrevNext=None), 400
       
    data = FromLogs.GetDataForMonth(year,month)

    calendar = FromLogs.CreateCalendar(year,month)

    PrevNext=Dates.PrevNextMonth(year, month)

    pagetitle=Dates.GetMonthString(year,month)

    return flask.render_template("data.html",months=months,hostname=hostname,calendar=calendar,data=data,DataTitle=pagetitle,PrevNext=PrevNext)


# Shows data for a particular day
@app.route("/data/<int:year>/<int:month>/<int:day>")
def DataForDayPage(year,month,day):

    months=FromLogs.GetAllMonths()

    #Check to see if the date is valid.
    try:
        datetime.date(year=year,month=month,day=day)
    except ValueError:
        return flask.render_template("data.html",months=months,hostname=hostname,DataTitle="Invalid Date",PrevNext=None), 400
        
    #refirect to the latest data page if the date requested is today
    if datetime.date.today() == datetime.date(year=year,month=month,day=day):
        return flask.redirect("/data")

    data = FromLogs.GetDataForDay(year,month,day)

    PrevNext=Dates.PrevNextDay(year, month,day)

    pagetitle="%04d-%02d-%02d"%(year,month,day)

    return flask.render_template("data.html",data=data,hostname=hostname,months=months,DataTitle=pagetitle,PrevNext=PrevNext)


#Request that we don't cache anything
def request_no_caching(response):
    response.headers["Cache-Control"]='no-cache, no-store, must-revalidate'
    response.headers["pragma"]='no-cache'
    response.headers["expires"]="0"
    return response



if __name__ == "__main__":
    app.run(host="0.0.0.0",port=5000)
