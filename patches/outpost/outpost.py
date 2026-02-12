#!/usr/bin/env python

# This module subscribes to MQTT to receive the temperature and humidity values 
# from a Tasmota zigbee2mqtt device. The received values are in JSON format and 
# are written to a CSV or TSV file.
#
# This software is part of the EEGsynth project, see <https://github.com/eegsynth/eegsynth>.
#
# Copyright (C) 2026 EEGsynth project
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import sys
import time
import paho.mqtt.client as mqtt
import json
import csv
import datetime

if hasattr(sys, 'frozen'):
    path = os.path.split(sys.executable)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__' and sys.argv[0] != '':
    path = os.path.split(sys.argv[0])[0]
    file = os.path.split(sys.argv[0])[-1]
    name = os.path.splitext(file)[0]
elif __name__ == '__main__':
    path = os.path.abspath('')
    file = os.path.split(path)[-1] + '.py'
    name = os.path.splitext(file)[0]
else:
    path = os.path.split(__file__)[0]
    file = os.path.split(__file__)[-1]
    name = os.path.splitext(file)[0]

# the lib directory contains shared code, like the EEGsynth module
# this python script is expected to be in the "patches/outpost" directory
sys.path.append(os.path.join(path, '../../src/lib'))
import EEGsynth


# The callback for when the client receives a CONNACK response from the server
def on_connect(client, userdata, flags, rc):
    monitor.info("Connected with result code " + str(rc))
    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    input_channels = patch.getstring('input', 'channels', default='#', multiple=True)
    for channel in input_channels:
        monitor.info('subscribed to ' + channel)
        client.subscribe(channel)


# The callback for when a PUBLISH message is received from the server
def on_message(client, userdata, msg):
    global monitor, csvwriter, f, fileformat

    # skip messages without JSON payload
    if not msg.payload.startswith(b'{'):
        return

    try:
        # decode the JSON payload
        monitor.debug("Received message on topic " + msg.topic + " with JSON payload " + str(msg.payload))
        payload = json.loads(msg.payload.decode('utf-8'))
        zbdata = payload.get('ZbReceived', None)
        if zbdata is not None:
            # zbdata is a dictionary, we need to iterate over its values
            for device_addr, device_data in zbdata.items():
                monitor.debug("Processing device " + device_addr + " with data " + str(device_data))
                if not isinstance(device_data, dict):
                    continue
                    
                Device = device_data.get('Device', None)
                Name = device_data.get('Name', None)
                if Device is None or Name is None:
                    continue

                # the measurement is timestamped
                DateTime = time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime()) 

                # get the individual values, use NaN if not present
                LinkQuality = device_data.get('LinkQuality', float('nan'))
                BatteryVoltage = device_data.get('BatteryVoltage', float('nan'))
                BatteryPercentage = device_data.get('BatteryPercentage', float('nan'))
                Temperature = device_data.get('Temperature', float('nan'))
                Humidity = device_data.get('Humidity', float('nan'))
                Pressure = device_data.get('Pressure', float('nan'))
                SeaPressure = device_data.get('SeaPressure', float('nan'))
                Illuminance = device_data.get('Illuminance', float('nan'))

                # write the data to file
                row = [DateTime, msg.topic, Device, Name, LinkQuality, 
                        BatteryPercentage, BatteryVoltage, Temperature, 
                        Humidity, Pressure, SeaPressure, Illuminance]
                
                csvwriter.writerow(row)
                f.flush()  # ensure data is written immediately

    except Exception as e:
        monitor.error("Error processing message on topic " + msg.topic + ": " + str(e))


# The callback for when the client disconnects
def on_disconnect(client, userdata, rc):
    if rc != 0:
        monitor.info("MQTT disconnected")


def _setup():
    '''Initialize the module
    This adds a set of global variables
    '''
    global patch, name, path, monitor, client, csvwriter, f, fileformat

    # configure and start the patch, this will parse the command-line arguments and the ini file
    patch = EEGsynth.patch(name=name, path=path)

    # this shows the splash screen and can be used to track parameters that have changed
    monitor = EEGsynth.monitor(name=name, patch=patch, debug=patch.getint('general', 'debug', default=1), target=patch.get('general', 'logging', default=None))

    try:
        client = mqtt.Client()
        client.connect(patch.get('mqtt', 'hostname'), 
                      patch.getint('mqtt', 'port', default=1883), 
                      patch.getint('mqtt', 'timeout', default=60))
    except Exception as e:
        monitor.error("Cannot connect to MQTT broker: " + str(e))
        raise RuntimeError("cannot connect to MQTT broker")
    
    filename = patch.getstring('recording', 'file')
    fileformat = patch.getstring('recording', 'format')
    if fileformat is None:
        # determine the file format from the file name
        name_part, ext = os.path.splitext(filename)
        if ext:
            fileformat = ext[1:].lower()
        else:
            fileformat = 'csv'  # default format
    
    # append the file name with a timestamp
    name_part, ext = os.path.splitext(filename)
    if len(ext) == 0:
        ext = '.' + fileformat
    fname = name_part + '_' + datetime.datetime.now().strftime("%Y.%m.%d_%H.%M.%S") + ext

    f = open(fname, 'w', newline='')
    
    if fileformat == 'csv':
        csvwriter = csv.writer(f, delimiter=',')
    elif fileformat == 'tsv':
        csvwriter = csv.writer(f, delimiter='\t')
    else:
        f.close()
        raise RuntimeError("unsupported file format: " + fileformat)

    # Write header row
    csvwriter.writerow(["datetime", "topic", "device", "name", "linkquality", 
                        "battery_percentage", "battery_voltage", "temperature", 
                        "humidity", "pressure", "sea_pressure", "illuminance"])

    f.flush()
    monitor.info("Writing to file: " + fname)


def _start():
    '''Start the module
    This uses the global variables from setup and adds a set of global variables
    '''
    global patch, name, path, monitor, client
    global prefix, output_scale, output_offset, input_channels

    # get the options from the configuration file
    prefix = patch.getstring('output', 'prefix', default='')

    # the scale and offset are used to map OSC values to Redis values
    output_scale = patch.getfloat('output', 'scale', default=1)
    output_offset = patch.getfloat('output', 'offset', default=0)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect

    client.loop_start()

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_once():
    '''Run the main loop once
    This uses the global variables from setup and start, and adds a set of global variables
    '''
    global patch, name, path, monitor, client
    global prefix, output_scale, output_offset

    # update the scale and offset
    output_scale = patch.getfloat('output', 'scale', default=1)
    output_offset = patch.getfloat('output', 'offset', default=0)

    # there should not be any local variables in this function, they should all be global
    if len(locals()):
        print('LOCALS: ' + ', '.join(locals().keys()))


def _loop_forever():
    '''Run the main loop forever
    '''
    global monitor, patch
    while True:
        monitor.loop()
        _loop_once()
        time.sleep(patch.getfloat('general', 'delay', default=1.0))


def _stop():
    '''Stop and clean up on SystemExit, KeyboardInterrupt, RuntimeError
    '''
    global monitor, client, f
    monitor.success("Stopping module...")
    if client:
        client.loop_stop(force=False)
        client.disconnect()
    if f:
        f.close()
    monitor.success("Done.")


if __name__ == '__main__':
    _setup()
    _start()
    try:
        _loop_forever()
    except (SystemExit, KeyboardInterrupt, RuntimeError):
        _stop()
    except Exception as e:
        monitor.error("Unexpected error: " + str(e))
        _stop()
        raise
    sys.exit()