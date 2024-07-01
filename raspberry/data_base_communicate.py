import psycopg2
from psycopg2 import Error
import time


class DB_actions():
	''' connect to database '''
	def connect_DB(self):
		try:
			#connection to data base
			conn = psycopg2.connect(dbname="tester", user="tester", password="postgres", host= "77.238.255.81", port="5432")
			
		except (Exception, Error) as error:
			print ("Error working table")
		finally:
			if conn:
				conn.close()
				#print ("stop connection DB")
	
	''' print data to the table on database '''		
	def send_data(self, imei, port):
		try:
			#connection to data base
			conn = psycopg2.connect(dbname="tester", user="tester", password="postgres", host= "77.238.255.81", port="5432")
			cur = conn.cursor()
			data_to_insert = (str(imei), str(time.perf_counter()), str(port))
			cur.execute("INSERT INTO devices VALUES (%s, %s, %s)", data_to_insert)
			conn.commit()
		
		except (Exception, Error) as error:
			print ("Error working table")
		finally:
			if conn:
				cur.close()
				conn.close()
			print ("stop connection DB")
	
	''' selsct data from database '''		
	def select(self):
		cur = conn.cursor()
		cur.execute('select * from devices')
		results = cur.fetchall()

		for result in results:
			print (result)
			
	def update(self):
		print ("update")
		
	def delete(self):
		print ("delete")
		
		
		
	
