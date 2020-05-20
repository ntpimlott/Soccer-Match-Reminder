import sys
import json
import requests
import http.client
from datetime import datetime
import pendulum
import mysql.connector
import smtplib
from email.message import EmailMessage
import os

fdata_api = os.environ['APIKEY']
headers = { 'X-Auth-Token': fdata_api }
connection = http.client.HTTPConnection('api.football-data.org')
ids= []
email_date = pendulum.datetime(1,1,1)
email_address = os.environ['E_USER']
email_password = os.environ['E_PWORD']

def checkdate(key):
    global headers
    global fdata_api
    global connection
    global email_date
    global ids

    connection.request('GET','/v2/teams/'+str(key)+'/matches?status=SCHEDULED',None,headers)
    matches = json.loads(connection.getresponse().read().decode())

    matches = matches["matches"]

    if len(matches) != 0:
        matches = matches[0]
        firstmatch = matches['utcDate']
        firstmatch = firstmatch[:-1]
        date = pendulum.from_format(firstmatch,'YYYY-MM-DDTHH:mm:ss',tz='Europe/London')
        date = date.in_timezone('America/Vancouver')
        email_date = date
        local_date = pendulum.now('America/Vancouver')
        difference = email_date.diff(local_date).in_hours()

        if difference < 30:
           return True

        else:
           return False

    else:
        return False


def pull_ids():
    global ids

    mydb = mysql.connector.connect(
        host=os.environ['AWSDBHOST'],
        user=os.environ['USER'],
        password=os.environ['PWORD'],
        database=os.environ['AWSDB']
    )

    mycursor = mydb.cursor()
    mycursor.execute("SELECT teamid FROM emails")
    myresult = mycursor.fetchall()

    for x in myresult:
        ids.append(x[0])

    ids = list(dict.fromkeys(ids))


def sendEmail(key):
    global email_date
    global ids
    global email_address
    global email_password

    emails_list = []

    mydb = mysql.connector.connect(
        host=os.environ['AWSDBHOST'],
        user=os.environ['USER'],
        password=os.environ['PWORD'],
        database=os.environ['AWSDB']
    )

    mycursor = mydb.cursor()
    sql = "SELECT emails FROM emails WHERE teamid = %s"
    newkey = (key,)
    mycursor.execute(sql,newkey)
    myresult = mycursor.fetchall()

    for x in myresult:
        emails_list.append(x[0])

    tn = "SELECT teamname FROM teams WHERE teamid = %s"
    mycursor.execute(tn,newkey)
    tname = mycursor.fetchall()

    msg = EmailMessage()
    msg['Subject'] = 'Soccer.py '+tname[0][0]+' Game Alert'
    msg['From'] = email_address
    msg.set_content('Game at'+str(email_date)+'lol')

    msg['To'] = ','.join(emails_list)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(email_address,email_password)
        smtp.send_message(msg)

    pass


def main(event=None, context=None):
    global connection
    global headers
    global ids

    pull_ids()

    for x in ids:
        y = checkdate(x)

        if y == True:
            sendEmail(x)
    pass

