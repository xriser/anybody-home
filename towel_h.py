# Towel heater with anybody home function
# Don't power on if nobody home

import paho.mqtt.client as mqtt #import the client1
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
import configparser
from apscheduler.schedulers.background import BackgroundScheduler
import os
import time
import re
import requests
import json
import argparse


dir_path = os.path.dirname(os.path.realpath(__file__))

config = configparser.ConfigParser()
config.read(dir_path + "/" + 'config.ini', encoding="utf8")
sections = config.sections()

InfluxDBHost     = config['settings']['InfluxDBHost']
InfluxDBPort     = config['settings']['InfluxDBPort']
InfluxDBUser     = config['settings']['InfluxDBUser']
InfluxDBPass     = config['settings']['InfluxDBPass']
InfluxDBDatabase = config['settings']['InfluxDBDatabase']

MqttHost = config.get('settings', 'MqttHost')
MqttPort = config.getint('settings', 'MqttPort')
MqttUser = config.get('settings', 'MqttUser')
MqttPass = config.get('settings', 'MqttPass')




def load_dirty_json(dirty_json):
    regex_replace = [(r"([ \{,:\[])(u)?'([^']+)'", r'\1"\3"'), (r" False([, \}\]])", r' false\1'), (r" True([, \}\]])", r' true\1')]
    for r, s in regex_replace:
        dirty_json = re.sub(r, s, dirty_json)
        clean_json = json.loads(dirty_json)
    return clean_json




def readInflux(query):
    #print(query)
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


def on_connect(mqttc, userdata, flags, rc):
    print("Connection returned result: "+str(rc))
    mqttc.subscribe("heater/power")

def on_subscribe(mqttc, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))


def on_message(mqttc, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)
    print("message qos=",message.qos)
    print("message retain flag=",message.retain)


def main():

    parser = argparse.ArgumentParser(description='Towel heater power on/off using anybody home info')
    parser.add_argument('-power','--power', help='use -power on/off', required=True)
    args = vars(parser.parse_args())

    mqttc = mqtt.Client()
    mqttc.on_connect = on_connect
    mqttc.on_message = on_message
    mqttc.on_subscribe = on_subscribe

    mqttc.username_pw_set(MqttUser, MqttPass)
    mqttc.connect(MqttHost, MqttPort, 60)
    mqttc.subscribe("heater/power")

    if args['power'] == 'on':
        query = readInflux("select count(*) from abh where time > now() - 1h tz('Europe/Kiev')")
        qdata = load_dirty_json(str(query.raw))
        # print(qdata)

        # list ['2018-06-30T21:34:07.839108789+03:00', 12, 12]
        # print(qdata['series'][0]['values'][0])
        list = qdata['series'][0]['values'][0]
        # sum all values
        sm = sum(list[1:len(list)])
        print(sm)

        # if sum all values = 0 - mean nobody home
        # TODO
        # 1. Merge with blink. Create project add disable switch: enable/disable autopoweroff
        if sm > 0:
            print('send POWER ON to Mqtt')
            mqttc.publish("heater/power", "1", retain=True)
            # value 1 - on

    if args['power'] == 'off':
        print('send POWER OFF to Mqtt')
        mqttc.publish("heater/power", "0", retain=True)

    #mqttc.loop_forever()
    #time.sleep(20)


if __name__ == "__main__":
    # execute only if run as a script
    main()
