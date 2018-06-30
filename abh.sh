#!/bin/sh


r3=$(iw dev wlan0 station dump |grep 'mac')

echo $r3

rn3=$(iw dev wlan0 station dump |grep 'mac')

echo $rn3


rn35=$(iw dev wlan1 station dump |grep 'mac')

echo $rn35





if [ -n "$r3" ]; then
 echo "r3 at home"
 #curl -i -XPOST http://10.0.0.7:8086/query --data-urlencode "q=CREATE DATABASE abh"
 curl -i -XPOST 'http://10.0.0.7:8086/write?db=abh' --data-binary 'abh,host=home,region=ua redmi=1'
fi

if [ -n "$rn3" ] || [ -n "$rn35" ]; then
 echo "rn3 at home"
 #curl -i -XPOST http://10.0.0.7:8086/query --data-urlencode "q=CREATE DATABASE abh"
 curl -i -XPOST 'http://10.0.0.7:8086/write?db=abh' --data-binary 'abh,host=home,region=ua redmin=1'
fi

