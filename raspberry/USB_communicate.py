import os
import time
import queue 
import serial
from threading import *
import data_base_communicate as db

command = "ATI+CGSN\r\n"
start_line = "+CGSN:"
baudrate = '115200'
usb_CH = "ttyCH"
usb_devices = []
timeout = 5				#timeout 5 sec
delta_time = 1

class USB_communicate():

	''' close USB connection ''' 
	def close_connect(self):
		serial_port.close()
		#print ("AT conection close")
		
	''' cheak usb devices '''
	def GetDevList(self): 
		return os.listdir("/dev")

	''' take usb list '''
	def GetCHDevices(self, _str):
		devOld = self.GetDevList()
		usb_devices = []
		for device in devOld:
			if _str in device:
				usb_devices.append("/dev/" + device)
		return usb_devices
	
	''' function for start thread '''
	def at_con(self, com_num):
		print ("Thread AT communicate start", com_num)
		self.at_read_write(com_num)

	''' detect imei '''
	def detect_ports(self, _str):  
		time.sleep(1)
		#take com-ports list
		comports_list = self.GetCHDevices(_str)
		
		if comports_list:
			print ("detected ", len(comports_list), "devices")
			#start threads for exist com-ports
			'''for port in comports_list:
				dev = Thread(target = self.at_con, args = (imei_in, port))
				dev.deamon = True
				dev.start()'''
		else:
			print ("comports list is empty")
		return comports_list
	
	''' read IMEI from modem '''		 
	def at_read_write(self, port_num):
		global timeout
		global delta_time
		to_print = 0
		#open serial conection NON Block (timeout = 0)
		serial_port = serial.Serial(port_num, baudrate, timeout = 0)
		
		if serial_port:
			#open com-port
			print ("open port: ", port_num)
			
			#flush tx and rx buffers
			serial_port.flushInput()
			serial_port.flushOutput()
			
			#send IMEI AT-command
			serial_port.write(command.encode())
			
			#flag for stop thread
			stop_thread = False
			
			#take start time
			start_time = time.perf_counter()
			round_time = time.perf_counter()
			
			#connect to DB
			data_base = db.DB_actions()
			data_base.connect_DB()
				
			#read GSM-module
			while (not stop_thread):			
				line = serial_port.readline()
		
				#cheak timeout
				if ((time.perf_counter() - start_time) > timeout):
					stop_thread = True
					serial_port.close()
				elif ((time.perf_counter() - round_time) > delta_time):
					round_time = time.perf_counter()
					#resend IMEI AT-command
					serial_port.write(command.encode())
					
				if (line):
					#errors of decode()
					try: 
						unicode_string = line.decode('utf-8')
					except UnicodeDecodeError:
						unicode_string = line.decode('utf-8', 'ignore')
					except serial.SerialException as se:
						print("Serial port error:", str(se))
					except serial.SerialTimeoutExcepction as ter:
						print ("Timeout error", str(ter))
						
					#read IMEI line	
					if (start_line in unicode_string):
						#print ("imei:", line)
						to_print = line[7: len(line)-2]
						print ("imei: ", to_print)
						#to_print_with_port = (port_num, to_print)
						#que_imei.put(to_print_with_port)
						
						#print to data-base
						data_base.send_data(to_print, port_num)
						
						#close com-port
						serial_port.close()
						
						#debug info
						print (port_num, ": conection close")
						stop_time = time.perf_counter()
						print (port_num, ": time stop: ", stop_time)
						delta = stop_time - start_time
						print (port_num, ": delta ", delta)
						#print ("queue: ", que_imei.qsize())
						
						stop_thread = True
									
			print ("Thread ", port_num, " close")
		else:
			print("close")
			to_print = 0
			
		return to_print
	
''' system cmd for ESP '''	
class system_cmd():
	''' cheak ESP chip '''
	def cheak_chip(self, port):
		return os.system("esptool.py --port " + str(port) + " chip_id")
	
	''' upload file to ESP '''
	def upload_file(self, chip, port, baud):
		f = open('path_to_file.txt', 'r')
		try:
			path = f.readline()
			print ("path to file:", path)
			f.close()
			finish_upload = False
			os.system ("esptool.py --chip " + str(chip) + " --port " + str(port) + " --baud " + str(baud) + " write_flash -z 0x00 " + path)
			finish_upload = True
			print ("finish upload")
		finally:
			f.close()
			
	'''read command from file'''
	def read_atcommands_from_file(self, path_to_file):
		open_file = open (path_to_file, "r")		#open file to read
		commands = open_file.readlines()			#read all lines as list
		open_file.close								#close file
		
		return commands								#return list of commands
		
	'''send command to processor'''
	def send_command(self, path_to_file, port_num, baudrate = 115200, timeout = 0):
		#read commands from file
		commands = self.read_atcommands_from_file(path_to_file)
		#open serial conection NON Block (timeout = 0)
		serial_port = serial.Serial(port_num, baudrate, timeout = 0)
		#if serial port opend
		if serial_port:
			#open com-port
			print ("open port: ", port_num)
			#flush tx and rx buffers
			serial_port.flushInput()
			serial_port.flushOutput()
			
			#if need wait answer from processor
			if timeout > 0:
				#calculate delta time to resend command
				delta_time = timeout//5
				#run commands from file
				for com in commands:
					#print command
					print(com.strip())
					#send AT-command from file
					serial_port.write(com.encode())
					#flag for stop waiting answer
					stop_waiting = False
					#take start time
					start_time = time.perf_counter()
					round_time = time.perf_counter()
					#read GSM-module
					while (not stop_waiting):			
						line = serial_port.readline()
						#cheak timeout
						if ((time.perf_counter() - start_time) > timeout):
							stop_waiting = True
							#serial_port.close()
						elif ((time.perf_counter() - round_time) > delta_time):
							round_time = time.perf_counter()
							#resend AT-command
							serial_port.write(com.encode())
						#if data in not empty	
						if (line):
							#errors of decode()
							try: 
								#decode input string
								unicode_string = line.decode('utf-8')
							except UnicodeDecodeError:
								unicode_string = line.decode('utf-8', 'ignore')
							except serial.SerialException as se:
								print("Serial port error:", str(se))
							except serial.SerialTimeoutExcepction as ter:
								print ("Timeout error", str(ter))								
							stop_waiting = True	
							'''take answer from library'''
							#debug info
							'''print (port_num, ": conection close")
							stop_time = time.perf_counter()
							print (port_num, ": time stop: ", stop_time)
							delta = stop_time - start_time
							print (port_num, ": delta ", delta)'''
			#if commands is moment
			elif timeout == 0:
				#run commands from file
				for com in commands:
					#print command
					print(com.strip())
					#send AT-command from file
					serial_port.write(com.encode())
					#wait time before send next command
					time.sleep(0.1)
				'''AT+DEBUG=1 send'''
				#send command to take status
				status_command = "AT+STATUS?"
				serial_port.write(status_command.encode())
				stop_waiting = False
				timeout = 5
				delta_time = timeout // 5
				#take start time
				start_time = time.perf_counter()
				round_time = time.perf_counter()
				#wait answer about status-device
				while (not stop_waiting):			
					line = serial_port.readline()
					#cheak timeout
					if ((time.perf_counter() - start_time) > timeout):
						stop_waiting = True
						#serial_port.close()
					elif ((time.perf_counter() - round_time) > delta_time):
						round_time = time.perf_counter()
						#resend AT-command
						serial_port.write(com.encode())
					#if data in not empty	
					if (line):
						#errors of decode()
						try: 
							#decode input string
							unicode_string = line.decode('utf-8')
						except UnicodeDecodeError:
							unicode_string = line.decode('utf-8', 'ignore')
						except serial.SerialException as se:
							print("Serial port error:", str(se))
						except serial.SerialTimeoutExcepction as ter:
							print ("Timeout error", str(ter))								
						stop_waiting = True	
						'''parse answer'''
						
		#close serial port	
		serial_port.close()


    



