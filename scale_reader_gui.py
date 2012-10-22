# -*- coding: utf-8 -*-
import serial
from time import sleep
import time
import re
import logging
import datetime
import pygtk
pygtk.require('2.0')
import gtk
import threading
import gobject

gobject.threads_init()

global RATE, LOCATIONS
RATE=9600
LOCATIONS=['/dev/ttyACM0','/dev/ttyUSB0','/dev/ttyUSB1','/dev/ttyUSB2','/dev/ttyUSB3',  
'/dev/ttyS0','/dev/ttyS2','/dev/ttyACM1','/dev/ttyS3'] 

class guiFramework(object):
    def __init__(self):
        self.window=gtk.Window(gtk.WINDOW_TOPLEVEL)
        self.window.set_title("Scale Measuring Program")
        self.window.connect("delete_event", self.delete_event)
        self.window.set_border_width(20)
        self.initializeSerial(None, None)
        self.details='No details were entered for this run.'
        self.speed='No speed was entered for this run.'
        self.guiInitialization()
        self.window.show_all()
        date=datetime.date.today()
        self.filename=str(date.month) +'-'+ str(date.day)
        self.filenumber=0
        self.initializeLogger()
        self.logging=False
        
    def initializeLogger(self):
            """Sets up logging"""
            self.logger=logging.getLogger('data_logger' + str(self.filenumber))
            self.hdlr = logging.FileHandler(self.filename + '-' +str(self.filenumber) + '.txt')
            self.formatter = logging.Formatter('%(message)s')  
            self.hdlr.setFormatter(self.formatter)
            self.logger.addHandler(self.hdlr)
            self.logger.setLevel(logging.WARNING) 
            self.basetime=float(time.time()) 
    
    def delete_event(self, widget, data=None):
        try: 
            self.Serial.close()
            print "Closing serial connection..."
        except:
            print "Serial connection alrady closed."
        
        gtk.main_quit()
        
    def guiInitialization(self):
        """Populates GUI window with buttons, graph, etc"""        
        self.bigHbox=gtk.HBox(False, 2)
        self.window.add(self.bigHbox)
        self.graphLogBox=gtk.VBox(True, 2)
        self.bigHbox.pack_start(self.graphLogBox, False, False, 0)
        self.dataBox=gtk.VBox(True,2)
        self.bigHbox.pack_start(self.dataBox, False, False, 0)
        
        self.serialbox=gtk.HBox(True, 2)
        self.graphLogBox.pack_start(self.serialbox, False, False, 0)
        
        self.serialConnectButton=gtk.Button('Connect to Scale')
        self.serialConnectButton.connect('clicked', self.serialConnect, '')
        self.serialDisconnectButton=gtk.Button('Disconnect from Scale')
        self.serialDisconnectButton.connect('clicked', self.serialDisconnect, '')
        """self.saveDataButton=gtk.Button('Save Data')
        self.saveDataButton.connect('clicked', self.saveData, None)"""
        self.serialbox.pack_start(self.serialConnectButton, False, False, 0)
        self.serialbox.pack_start(self.serialDisconnectButton, False, False, 0)
        """self.serialbox.pack_start(self.saveDataButton, False, False, 0)"""
        
        self.textFrame=gtk.Frame('Run details')
        self.graphLogBox.pack_start(self.textFrame, False, False, 0)
        self.detailEntry=gtk.Entry(200)
        self.detailEntry.connect('activate', self.getDetailText, '')
        self.textFrame.add(self.detailEntry)
        
        self.speedFrame=gtk.Frame('Run Speed (fpm)')
        self.graphLogBox.pack_start(self.speedFrame, False, False, 0)
        self.speedEntry=gtk.Entry(3)
        self.speedEntry.connect('activate',self.getSpeedText, '')
        self.speedFrame.add(self.speedEntry)
        
        self.loggingbox=gtk.HBox(True, 2)
        self.graphLogBox.pack_start(self.loggingbox, False, False, 0)
        self.beginLoggingButton=gtk.Button('Begin Logging')
        self.beginLoggingButton.connect('clicked', self.startLogging, '')
        self.stopLoggingButton=gtk.Button('Stop Logging')
        self.stopLoggingButton.connect('clicked', self.stopLogging, '')
        self.newFileButton=gtk.Button('Use New File')
        self.newFileButton.connect('clicked', self.newFile, None)
        self.loggingbox.pack_start(self.beginLoggingButton, False, False, 0)
        self.loggingbox.pack_start(self.stopLoggingButton, False, False, 0)
        self.loggingbox.pack_start(self.newFileButton, False, False, 0)
        
        self.dashboardbox=gtk.HBox(True, 2)
        self.weightFrame=gtk.Frame('Current Weight')
        self.weightLabel=gtk.Label('No data yet...')
        self.weightFrame.add(self.weightLabel)
        self.loggingFrame=gtk.Frame('Logging Status')
        self.loggingLabel=gtk.Label('Not logging')
        self.loggingFrame.add(self.loggingLabel)
        self.graphLogBox.pack_start(self.dashboardbox, False, False, 0)
        self.dashboardbox.pack_start(self.weightFrame, False, False, 0)
        self.dashboardbox.pack_start(self.loggingFrame, False, False, 0)
        
    def initializeSerial(self, widget, data):
        global LOCATIONS, RATE
        for name in LOCATIONS:
            try:
                self.Serial=serial.Serial(name, RATE)
                self.monitorThread=gtkThread(self)
                self.monitorThread.start()
                print 'Connected on ' + name
                break
            except:
                print 'Failed to connect on ' + name
    
    def serialConnect(self, widget, data):
        self.initializeSerial('', '')
    
    def serialDisconnect(self, widget, data):
        try:
            self.Serial.close()
            self.monitorThread.quit=True
        except:
            print 'Port never connected'
            
    """def saveData(self, widget, data):
        logger.setlevel(logging.INFO)
        logger.info(self.details)"""
    
    def getDetailText(self, widget, data):
        self.details=self.detailEntry.get_text()
        if not self.details:
            self.details='No details were entered for this run.'
    
    def getSpeedText(self, widget, data):
        self.speed=self.speedEntry.get_text()
        if not self.speed:
            self.speed='No speed was entered for this run.'
    
    def startLogging(self, widget, data):
        self.logger.setLevel(logging.INFO)
        self.getDetailText('','')
        self.getSpeedText('','')
        self.logger.info('Begin data segment')
        self.logger.info(str(datetime.datetime.now()))
        self.logger.info(self.details + ' ' + self.speed)
        self.basetime=float(time.time())
        self.logging=True
        self.loggingLabel.set_text("Logging")
    
    def stopLogging(self, widget, data):
        self.logger.info('End segment') 
        self.logger.setLevel(logging.WARNING)
        self.logging=False
        self.loggingLabel.set_text("Not Logging")
    
    def newFile(self, widget, data):
        self.filenumber+=1
        self.initializeLogger()
        if self.logging==True:
            self.logger.setLevel(logging.INFO)

class linearRegressor(object):
    def __init__(self, xdata, ydata):
        self.xdata=[]
        self.ydata=[]
        for i in range(len(xdata)):
            self.xdata.append(float(xdata[i]))
            self.ydata.append(float(ydata[i]))
        self.N=len(ydata)
        self.slope=0.0
        self.intercept=0.0
        self.xsum=0
        self.ysum=0
        self.min=2
        self.max=40
        self.SSE=0.
        self.TSS=0.
        self.rr=0.0
        
    def update(self, xdata, ydata):
        self.xdata.append(xdata)
        self.ydata.append(ydata)
        self.N=len(ydata)
        if self.min < len(ydata):
            self.regress()
            self.QC()
            if self.max < len(ydata):
                self.xdata.reverse()
                self.ydata.reverse()
                self.xdata.pop()
                self.ydata.pop()
                self.xdata.reverse()
                self.ydata.reverse()
            
        
    def regress(self):
        if sum(self.xdata)*sum(self.ydata) != 0:
            test=5
        self.N=len(self.ydata)
        self.xsum=sum(self.xdata)
        self.ysum=sum(self.ydata)
        self.xysum=0.0
        self.xxsum=0.0
        self.yysum=0.0
        for i in range(self.N):
            self.xysum+=self.xdata[i]*self.ydata[i]
            self.xxsum+=self.xdata[i]**2
            self.yysum+=self.ydata[i]**2
        
        self.intercept=(self.ysum*self.xxsum-self.xsum*self.xysum)/(self.N*self.xxsum-self.xsum**2)
        self.slope=(self.N*self.xysum-self.xsum*self.ysum)/(self.N*self.xxsum-self.xsum**2)
    
    def QC(self):
        self.TSS=0.0
        self.SSE=0.0
        average=self.ysum/self.N
        for i in range(self.N):
            Yi=(self.xdata[i]*self.slope+self.intercept)
            self.TSS+=(average-ydata[i])**2
            self.SSE+=(self.ydata[i]-Yi)**2
        self.rr=1-self.SSE/self.TSS

            
        
class gtkThread(threading.Thread):
    def __init__(self, gui):
        super(gtkThread, self).__init__()
        self.gui=gui
        self.label=gui.weightLabel
        self.quit=False
        self.Serial=self.gui.Serial
        
    def update_label(self, weight):
        self.label.set_text(weight)
        return False
        
    def run(self):
        while not self.quit:
            data_in=''
            char=''
            weight=''
            average=0.0
            self.Serial.flushInput()
            i=0
            regex='[0-9]+(\.[0-9][0-9][0-9]?)?'
            while i<20:
                weight=''
                while not weight:
                    data_in=self.Serial.readline()
                    a=re.split(' ', data_in)
                    for string in a:
                        try:
                            m=re.match(regex, string)
                            weight=float(m.group())
                        except:
                            char=string
                average+=weight/20.0
                self.Serial.flushInput()
                sleep(.05)
                i+=1
            gobject.idle_add(self.update_label,str(average))
            elapsed=float(time.time())-self.gui.basetime
            gui.logger.info(str(elapsed)[:4] + ' ' + str(average))
            
class gtkRegressionThread(threading.Thread):
    def __init__(self, gui):
        super(gtkRegressionThread, self).__init__()
        self.gui=gui
        self.label=gui.weightLabel
        self.quit=False
        
    def update_label(self, weight):
        self.label.set_text(weight)
        return False
        
    def run(self):
        while not self.quit:
            data_in=''
            char=''
            weight=''
            average=0.0
            self.Serial.flushInput()
            i=0
            regex='[0-9]+(\.[0-9][0-9][0-9]?)?'
            while i<20:
                weight=''
                while not weight:
                    data_in=self.Serial.readline()
                    a=re.split(' ', data_in)
                    for string in a:
                        try:
                            m=re.match(regex, string)
                            weight=float(m.group())
                        except:
                            char=string
                average+=weight/20.0
                self.Serial.flushInput()
                sleep(.05)
                i+=1
            gobject.idle_add(self.update_label,str(average))
            elapsed=float(time.time())-self.gui.basetime
            gui.logger.info(str(elapsed)[:4] + ' ' + str(average))
        

gui=guiFramework()

gtk.main()
"""
xdata=[43, 21, 25, 42, 57, 59]
ydata=[99, 65, 79, 75, 87, 81]
#xdata=[0,1,2,3,4,5]
#ydata=[0,2,4,6,8,10.1]
line=linearRegressor(xdata, ydata)
line.regress()
line.QC()
print line.slope
print line.intercept
print line.rr
"""