#!/usr/bin/env python

import obd_io
import serial
import platform
import obd_sensors
import json
import socket    #&L Added socket library

from datetime import datetime
import time

from obd_utils import scanSerial

class OBD_Capture():
    def __init__(self):
        self.port = None
        self.soc = None #&L add socket as member
        localtime = time.localtime(time.time())

    def socConnect(self): #&L Added function to connect to host. We should probably change the port. Also, we should propbably add some error checking.
        HOST = '203.42.134.229'    # The remote host. Correct address.
        PORT = 50007              # The same port as used by the server
        self.soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        soc.connect((HOST, PORT))    #&L Will fail if server does not accept. Might be worth trying on a local network.
        #&J I am pretty sure some sort of authentication will be needed here when connecting to the server ??

    def socIsConnected(self):
        return self.soc;

    def connect(self):
        portnames = scanSerial()
        print portnames
        for port in portnames:
            self.port = obd_io.OBDPort(port, None, 2, 2)
            if(self.port.State == 0):
                self.port.close()
                self.port = None
            else:
                break

        if(self.port):
            print "Connected to "+self.port.port.name
            
    def is_connected(self):
        return self.port
        
    def capture_data(self):

        #Find supported sensors - by getting PIDs from OBD
        # its a string of binary 01010101010101 
        # 1 means the sensor is supported
        self.supp = self.port.sensor(0)[1]
        self.supportedSensorList = []
        self.unsupportedSensorList = []

        # loop through PIDs binary
        for i in range(0, len(self.supp)):
            if self.supp[i] == "1":
                # store index of sensor and sensor object
                self.supportedSensorList.append([i+1, obd_sensors.SENSORS[i+1]])
            else:
                self.unsupportedSensorList.append([i+1, obd_sensors.SENSORS[i+1]])
        
        for supportedSensor in self.supportedSensorList:
            print "supported sensor index = " + str(supportedSensor[0]) + " " + str(supportedSensor[1].shortname)        
        
        time.sleep(3)
        
        if(self.port is None):
            return None

        #Loop until Ctrl C is pressed        
        try:
            while True:
                json_data = []
                localtime = datetime.now()
                current_time = str(localtime.hour)+":"+str(localtime.minute)+":"+str(localtime.second)+"."+str(localtime.microsecond)
                json_data.append({'Time':current_time})
                results = {}
                for supportedSensor in self.supportedSensorList:
                    sensorIndex = supportedSensor[0]
                    (name, value, unit) = self.port.sensor(sensorIndex)
                    json_data.append({name:value + ' ' + unit})

                #print json.dumps(json_data)     #SEND THIS TO SERVER PERIODICALLY (Single packet of information)
                self.soc.send(json.dumps(json_data))    #&L Send to server.
                time.sleep(0.5)                 #Should probably iterate a few times befo

        except KeyboardInterrupt:
            self.port.close()
            print("stopped")

if __name__ == "__main__":

    o = OBD_Capture()
    o.connect()
    o.socConnect()    #&L Added code to connect to server.
    time.sleep(3)
    if ( not o.is_connected() ): #&L Added check for socket; don't run if se
        print "Not connected to OBD Dongle"
    elif ( not o.socIsConnected() ): #&J Altered for mre accurate debug
        print "Not connected to Server"
    else:
        o.capture_data()