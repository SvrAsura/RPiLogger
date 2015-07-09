## This code for T100, ELT CO2 sensor
## Please see details for the CO2 sensor : ....

import serial,os,time
import sys
import RPi.GPIO as GPIO
import logging 
import logging.handlers 

import json
import requests
import fcntl, socket, struct

DEBUG_PRINT = 1
SERIAL_READ_BYTE = 12
FILEMAXBYTE = 1024 * 1024 * 100 #100MB
LOG_PATH = '/home/pi/log_tos.log'

# important, sensorname shuould be pre-defined, unique sensorname
sensorname = "co2.test"

#url = "http://127.0.0.1:4242/api/put"
url = "http://125.7.128.53:4242/api/put"

def getHwAddr(ifname):
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	info = fcntl.ioctl(s.fileno(), 0x8927, struct.pack('256s', ifname[:15]))
	return ':'.join(['%02x' %ord(char) for char in info[18:24]])

macAddr = getHwAddr('eth0')
macAddr = macAddr.replace(':','.')

level = 0
ppm = 0

def led0On():
	#GPIO.output(6, True)
	GPIO.output(17, True)
def led1On():
	#GPIO.output(13, True)
	GPIO.output(22, True)
def led2On():
	#GPIO.output(19, True)
	GPIO.output(27, True)

def led0Off():
	#GPIO.output(6, False)
	GPIO.output(17, False)
def led1Off():
	#GPIO.output(13, False)
	GPIO.output(22, False)
def led2Off():
	#GPIO.output(19, False)
	GPIO.output(27, False)
def ledAllOff():
	led0Off()
	led1Off()
	led2Off()
def ledAllOn():
	led0On()
	led1On()
	led2On()

def rled0On():
	led0Off()
def rled1On():
	led1Off()
def rled2On():
	led2Off()

def rled0Off():
	led0On()
def rled1Off():
	led1On()
def rled2Off():
	led2On()
def rledAllOff():
	ledAllOn()
def rledAllOn():
	ledAllOff()

def rled0Blink():
	led0On()
	time.sleep(0.5)
	led0Off()
	time.sleep(0.3)
	led0On()
	time.sleep(0.5)
	led0Off()
	time.sleep(0.3)
	led0On()
def rled1Blink():
	led1On()
	time.sleep(0.5)
	led1Off()
	time.sleep(0.3)
	led1On()
	time.sleep(0.5)
	led1Off()
	time.sleep(0.3)
	led1On()
def rled2Blink():
	led2On()
	time.sleep(0.5)
	led2Off()
	time.sleep(0.3)
	led2On()
	time.sleep(0.5)
	led2Off()
	time.sleep(0.3)
	led2On()

# check length, alignment of incoming packet string
def syncfind():
	index = 0
	alignment = 0
	while 1:
		in_byte = serial_in_device.read(1)
# packet[8] should be 'm'
# end of packet is packet[10]
		if in_byte is 'm' :
			#print 'idx =', index, in_byte
			alignment = 8
		if alignment is 10 : 
			alignment = 1
			index = 0
			break
		elif alignment > 0 :
			alignment += 1
		index += 1

def checkAlignment(incoming):
	idxNum = incoming.find('m')
	# idxNum is 9, correct
	offset = idxNum - 9	
	if offset > 0 :
		new_str = incoming[offset:]
		new_str = new_str + incoming[:offset]
	if offset < 0 :
		offset = 12 + offset 
		new_str = incoming[offset:]
		new_str = new_str + incoming[:offset]
	return new_str
	
def init_process():
	print " "
	print "MSG - [S100, T110 CO2 Sensor Driver on RASPI2, Please check log file : ", LOG_PATH
	print "MSG - now starting to read SERIAL PORT"
	print " "
	# HW setup, GPIO
	GPIO.setwarnings(False)
	GPIO.cleanup()
	GPIO.setmode(GPIO.BCM)
	#GPIO.setup(6, GPIO.OUT)
	GPIO.setup(17, GPIO.OUT)
	#GPIO.setup(13, GPIO.OUT)
	GPIO.setup(27, GPIO.OUT)
	#GPIO.setup(19, GPIO.OUT)
	GPIO.setup(22, GPIO.OUT)
	logger.info(' *start* GPIO all set, trying to open serial port, SW starting ')
	rledAllOn()

######################################################################
# START Here. Main
######################################################################

# set logger file
logger = logging.getLogger(sensorname)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

fileHandler = logging.handlers.RotatingFileHandler(LOG_PATH, maxBytes=FILEMAXBYTE,backupCount=10)
fileHandler.setLevel(logging.DEBUG)
fileHandler.setFormatter(formatter)
logger.addHandler(fileHandler)

#consoleHandler = logging.StreamHandler()
#consoleHandler.setLevel(logging.DEBUG)
#consoleHandler.setFormatter(formatter)
#logger.addHandler(consoleHandler)

# call raspi init...
init_process()

# open RASPI serial device, 38400
try:
	serial_in_device = serial.Serial('/dev/ttyAMA0',38400)
except serial.SerialException, e:
	logger.error("Serial port open error")
	rled0Off()
	rled1Off()
	rled2Off()

while 1:
	ppm = 0
	try:
		in_byte = serial_in_device.read(SERIAL_READ_BYTE) 
		pos = 0
	except serial.SerialException, e:
		rled0Off()
		rled1Off()
		rled2Off()
	if not (len(in_byte) is SERIAL_READ_BYTE) : 
		logger.error("Serial packet size is strange, %d, expected size is %d" % (len(in_byte),SERIAL_READ_BYTE))
		print 'serial byte read count error'
		continue
	# sometimes, 12 byte alighn is in-correct
	# espacially run on /etc/rc.local
	if not in_byte[9] is 'm':
		shift_byte = checkAlignment(in_byte)
		in_byte = shift_byte
		
	if ('ppm' in in_byte):
		if DEBUG_PRINT :
			print '-----\/---------\/------ DEBUG_PRINT set -----\/---------\/------ '
			for byte in in_byte :
				print "serial_in_byte[%d]: " %pos,
				pos += 1
				if ord(byte) is 0x0d :
					print "escape:", '0x0d'," Hex: ", byte.encode('hex')
					continue
				elif ord(byte) is 0x0a :
					print "escape:", '0x0a'," Hex: ", byte.encode('hex')
					continue
				print " String:", byte,  "    Hex: ", byte.encode('hex')
		if not (in_byte[2] is ' ') :
			ppm += (int(in_byte[2])) * 1000
		if not (in_byte[3] is ' ') :
			ppm += (int(in_byte[3])) * 100
		if not (in_byte[4] is ' ') :
			ppm += (int(in_byte[4])) * 10
		if not (in_byte[5] is ' ') :
			ppm += (int(in_byte[5]))  

		logline = sensorname + ' CO2 Level is '+ str(ppm) + ' ppm' 
		#now = time.localtime()
		#now_str = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
		#logline += now_str
		if DEBUG_PRINT :
			print logline
		if ppm > 2500 : 
			logger.error("%s", logline)
			continue
		else :
			logger.info("%s", logline)

        print "macAddr : " + macAddr
        
        data = {
			"metric": "rc1.co2.ppm",
			"timestamp": time.time(),
			"value": ppm,
			"tags": {
				"eth0": macAddr,
				"hw": "raspberrypi2" ,
				"sensor" : "co2.t110",
				"name" : sensorname,
				"floor_room": "10fl_min_room",
				"building": "woosung",
				"owner": "kang",
				"country": "kor"
			}
			#tags should be less than 9, 8 is alright, 9 returns http error
		}
        
        #try :
		#	ret = requests.post(url, data=json.dumps(data))
		#	logger.info("http ret %s", ret)
		#	if DEBUG_PRINT :
		#		print "http return : %s" %ret
        #except requests.exceptions.Timeout :
		#	logger.error("http connection error, Timeout  %s", ret)
		#	continue;
        #except requests.exceptions.ConnectionError :
		#	logger.error("http connection error, Too many requests %s", ret)
		#	continue;
        

# level = 1, 0~1000 ppm,    no- LED
# level = 2, 1000~1150 ppm, 1 - LED
# level = 3, 1150~1300 ppm, 2 - LED
# level = 4, 1300~1700 ppm, 3 - LED
# level = 5, 1750~ ppm,     4 - LED

	if ppm < 800 :  
		rled0Blink()
		rled0Blink()
		rled0Blink()
		led1Off()
		led2Off()
	elif ppm < 1000 :  
		led0On()
		led1Off()
		led2Off()
	elif ppm < 1300 :  
		led0Off()
		led1On()
		led2Off()
	elif ppm < 1600:  
		led0On()
		led1Off()
		led2On()
	elif ppm < 1900:  
		led0Off()
		led1Off()
		led2On()
	elif ppm >= 1900 :  
		led0Off()
		led1Off()
		rled2Blink()
		rled2Blink()
		rled2Blink()

GPIO.cleanup()


