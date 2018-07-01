from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
import configparser
from apscheduler.schedulers.background import BackgroundScheduler
import os
import time
import re
import requests
import json
#from blynkapi import Blynk


dir_path = os.path.dirname(os.path.realpath(__file__))

config = configparser.ConfigParser()
config.read(dir_path + "/" + 'config.ini', encoding="utf8")
sections = config.sections()

InfluxDBHost     = config['settings']['InfluxDBHost']
InfluxDBPort     = config['settings']['InfluxDBPort']
InfluxDBUser     = config['settings']['InfluxDBUser']
InfluxDBPass     = config['settings']['InfluxDBPass']
InfluxDBDatabase = config['settings']['InfluxDBDatabase']

BlynkUrl    = config.get('settings', 'BlynkUrl')
BlynkPort   = config.get('settings', 'BlynkPort')
BlynkToken  = config.get('settings', 'BlynkToken')

#auth_token = BlynkToken

#server = "10.0.0.7"
#protocol = "http"
#port = "8080"

# create objects
#Blynk(token, server, protocol, port, pin, value)
#wh_autopower = Blynk(token=auth_token, server='10.0.0.7', protocol="http", port="8080", pin = "V1")
#res = wh_autopower.get_val()
#print(res)


def load_dirty_json(dirty_json):
    regex_replace = [(r"([ \{,:\[])(u)?'([^']+)'", r'\1"\3"'), (r" False([, \}\]])", r' false\1'), (r" True([, \}\]])", r' true\1')]
    for r, s in regex_replace:
        dirty_json = re.sub(r, s, dirty_json)
        clean_json = json.loads(dirty_json)
    return clean_json

def timer1():
    #check autopoweroff button

    #res = wh_autopower.get_val()
    value  = getBlynkValue("V1")
    autopower = int(value[2])
    #powerstate 0 - powered on
    value = getBlynkValue("V0")
    powerstate = int(value[2])
    # response string ["0"] or ["1"]
    #print(autopower)
    #print(powerstate)

    if autopower == 1:

        #check anybody home last 30m
        query = readInflux("select count(*) from abh where time > now() - 30m tz('Europe/Kiev')")
        qdata = load_dirty_json(str(query.raw))
        # print(qdata)

        # list ['2018-06-30T21:34:07.839108789+03:00', 12, 12]
        # print(qdata['series'][0]['values'][0])
        list = qdata['series'][0]['values'][0]
        # sum all values
        sm = sum(list[1:len(list)])
        #print(sm)

        # if sum all values = 0 - mean nobody home
        # 1. should check state first.
        # 2. add disable switch to blynk: enable/disable autopoweroff
        if sm == 0:
            print('send to Blynk water heater off')
            # value 1 - hash from Blynk config - project waterheater, water heater off
            post_2blynk('V0', '1')
        if sm > 0 and powerstate == 1:
            print('send to Blynk water heater on')
            post_2blynk('V0', '0')


def getBlynkValue(pin):
    try:
        response = requests.get(BlynkUrl + ':' + BlynkPort + '/' + BlynkToken + '/get/' + pin, timeout=(15, 15))
        response.raise_for_status()

    except requests.exceptions.ReadTimeout:
        print('Oops. Read timeout occured')

    except requests.exceptions.ConnectTimeout:
        print('Oops. Connection timeout occured!')

    except requests.exceptions.ConnectionError:
        print('Seems like dns lookup failed..')

    except requests.exceptions.HTTPError as err:
        print('Oops. HTTP Error occured')
        print('Response is: {content}'.format(content=err.response.content))

    #print("Response status code: " + str(response.status_code))
    text = response.text
    return text




def post_2blynk(pin, pin_value):
    #print("Check response...")
    try:
        response = requests.get(BlynkUrl + ':' + BlynkPort + '/' + BlynkToken + '/update/' + pin + '?value='+ pin_value, timeout=(15, 15))
        response.raise_for_status()

    except requests.exceptions.ReadTimeout:
        print('Oops. Read timeout occured')

    except requests.exceptions.ConnectTimeout:
        print('Oops. Connection timeout occured!')

    except requests.exceptions.ConnectionError:
        print('Seems like dns lookup failed..')

    except requests.exceptions.HTTPError as err:
        print('Oops. HTTP Error occured')
        print('Response is: {content}'.format(content=err.response.content))

    #print("Response status code: " + str(response.status_code))
    text = response.text



def readInflux(query):
    result = ''
    try:
        client = InfluxDBClient(InfluxDBHost, InfluxDBPort, InfluxDBUser, InfluxDBPass, InfluxDBDatabase, timeout=10)
    except Exception as err:
        flash("Influx connection error: %s" % str(err))
    if client:
        #print("Read points:")
        try:
            result = client.query(query)
        except Exception as err:
            print('InfluxDBClientError = ' + str(err))
    return result




def main():

    scheduler = BackgroundScheduler()
    scheduler.add_job(timer1, 'interval', seconds=5)
    scheduler.start()


    while True:
        time.sleep(1)


if __name__ == "__main__":
    # execute only if run as a script
    main()
