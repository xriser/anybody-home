# anybody-home
Check if anybody at home and poweroff devices


Will check anybody home by mobile devices connected to home WiFi

1. Get your devices mac address
2. Put check script abh.sh to router crontab

#!/bin/sh
r3=$(iw dev wlan0 station dump |grep 'device_mac')

3. Write results to database
curl -i -XPOST 'http://10.0.0.7:8086/write?db=abh' --data-binary 'abh,host=home,region=ua redmin=1'

4. Check database for data last hour

select count(*) from abh where time > now() - 1h

if result = 0 poweroff something.

