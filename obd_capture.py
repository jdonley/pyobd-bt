#!/usr/bin/env python

import obd_io
import serial
import base64    #&L Added for authentication
import platform
import obd_sensors
import json
import socket    #&L Added socket library
import urllib2   #MJ Added url library (urllib) ---If Python 2.x use urllib2
import httplib

#JD.. the raspberry pi had python 2.7 installed so left it at that and changed this code a little

from datetime import datetime
import time

from obd_utils import scanSerial

class OBD_Capture():
    def __init__(self):
        self.port = None
        localtime = time.localtime(time.time())
        httplib.HTTPConnection._http_vsn = 10
        httplib.HTTPConnection._http_vsn_str = 'HTTP/1.0'
        #self.server_url = 'http://203.42.134.229/api/v1/logs'    #JD. Added global URL string
        self.server_url = 'http://home.adebono.com/m2m/api/v1/logs'
        self.auth_string = base64.encodestring('%s:%s' % ('uow', 'm2muow')) #&L Needs to be changed to a real user. #JD. Changed to self.auth_string

    def testServerConnection(self):    #JD. Mock up data to test transmission   
        try:    
            json_data = {}    
            json_data.update({'car_id':'1'})    
            json_data.update({'time':str(int(time.time()))})
            json_data.update({'Fuel System Status':0400})
            json_data.update({'Coolant Temp (C)':59})
            json_data.update({'Engine RPM':970})
            json_data.update({'Timing Advance (degrees)':8.0})
            json_data.update({'Air Flow Rate (MAF) (lb/min)':0.44444736})
            request = urllib2.Request(self.server_url)   
#            request.add_header("Authorization", "Basic %s" % self.auth_string) 
            request.add_header('Content-Type', 'application/json')
            print '['+json.dumps(json_data, sort_keys=True, indent=2)+']'
            response = urllib2.urlopen(request,'['+json.dumps(json_data, sort_keys=True)+']')
            print "Successfully Sent HTTP Packet"
        except urllib2.HTTPError as ex:
            print "Failed to HTTP POST: " + str(ex.code)+" " + str(ex.reason)
        

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
                self.supportedSensorList.update([i+1, obd_sensors.SENSORS[i+1]])
            else:
                self.unsupportedSensorList.update([i+1, obd_sensors.SENSORS[i+1]])
        print "\n--- Supported OBDII PIDs ---"
        print "Index \t Name"
        for supportedSensor in self.supportedSensorList:
            print str(supportedSensor[0]) + "\t" + str(supportedSensor[1].shortname)        
        
        time.sleep(1)
        
        if(self.port is None):
            return None

        #Loop until Ctrl C is pressed        
        try:
            while True:
                try:
                    json_data = {}    #JD
                    localtime = datetime.now()
                    current_time = str(localtime.hour)+":"+str(localtime.minute)+":"+str(localtime.second)+"."+str(localtime.microsecond)
                    print current_time
                    json_data.update({'time':str(int(time.time()))})    #JD
                    json_data.update({'car_id':'1'})    #JD
                    results = {}
                    for supportedSensor in self.supportedSensorList:
                            sensorIndex = supportedSensor[0]
                            (name, value, unit) = self.port.sensor(sensorIndex)
                            json_data.update({name:value})    #JD   fixed str and list issue
                            print name + " = " + str(value) +" "+ unit        #JD. Comment this line out when not debugging
                
                    print "\n"+'['+json.dumps(json_data, sort_keys=True, indent=2)+']'         #JD SEND THIS TO SERVER PERIODICALLY (Single packet of information) #JD. Comment this line out when not debugging

                    #------------------------Mitch's Code------------------------
                    #Crease a http request, chuck in the correct address when adam gives us one
                    request = urllib2.Request(self.server_url)    #JD Added IP address, will assume saving to home directory
                    #Add authentication.
                    request.add_header("Authorization", "Basic %s" % self.auth_string) #&L Added authentication header. #JD. Changed to self.auth_string
                    #Assume that we have to do proper http, so add a header specifying that it's json
                    request.add_header('Content-Type', 'application/json')
                    #Send the request and attach the raw json data
                    response = urllib2.urlopen(request,'['+json.dumps(json_data, sort_keys=True, indent=2)+']')
                    #----------------------------End-----------------------------
                
                    time.sleep(0.5)                 #Should probably iterate a few times before sending json data
                    
                #JD. Handling this exception inside the loop allows for continuation of OBD-reading upon loss of server connection 
                except urllib2.HTTPError as ex:     #JD. Added HTTP exception handling
                    print "Failed to upload to server: " +str(ex.code) + " " + str(ex.reason)

        except KeyboardInterrupt:
            self.port.close()
            print("Stopped")

if __name__ == "__main__":

    o = OBD_Capture()
    o.testServerConnection()    #JD. Sends mock data to server to test connection. Comment out when not debugging
    o.connect()
    
    time.sleep(1)
    if ( not o.is_connected() ):
        print "Not connected to OBD Dongle"
    else:
        o.capture_data()