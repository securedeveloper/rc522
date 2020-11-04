#!/usr/bin/env python

import datetime
import pymysql
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()
GPIO.setwarnings(False)
db = pymysql.connect("localhost","adminuser","raspberry","studentsdb")

def select_user_data(tag):
	cursor = db.cursor()
	cursor.execute("SELECT * FROM students WHERE uid = '"+tag+"'")
	return cursor.fetchone()

def input_user_data():
	choice = input("Would you like to enter new record? [Y/n]")
	if(choice.lower() == 'y'):
		name=input("Enter student name:")
		return True, name
	else:
		return False, None
		
def create_new_user(name, uuid):
	with db.cursor() as cursor:
		sql = "INSERT INTO `students`(`uid`, `name`, `registered_at`) VALUES ('%s','%s', now())" % (uuid, name)
		cursor.execute(sql)
	db.commit()
	with db.cursor() as cursor:
		sql = "SELECT LAST_INSERT_ID()"
		cursor.execute(sql)
		result = cursor.fetchone()
		if(result):
			print("Student registered successfully with ID: %s" % (result))
		else:
			print("Student could not registered, try again!")
		
def update_user_attendance_time(user):
	non_reacting_time = 20 #if any activity within these many second do not update any data
	id,uid,name,reg_time,login_at,logout_at,logged_status,last_updated = user
	sql = ""
	if(logged_status.lower() == "out"): #Login the user
		sql = "UPDATE `students` SET `login_at`=now(),`logged_status`='In' WHERE `uid` = '"+uid+"' AND TIMESTAMPDIFF(SECOND,logout_at, NOW()) > "+non_reacting_time
	else: #Logout the user
		sql = "UPDATE `students` SET `logout_at`=now(),`logged_status`='Out' WHERE `uid` = '"+uid+"' AND TIMESTAMPDIFF(SECOND,login_at, NOW()) > "+non_reacting_time
	print(sql)
	with db.cursor() as cursor:
		cursor.execute(sql)
	db.commit()
	dt = datetime.datetime.now()
	print("%s record updated successfully @ %s" % (name, logged_status, dt.strftime("%x %X")))

try:
	count = 0
	while True:
		print("\n\nScanning...")
		count += 1
		x = datetime.datetime.now()
		tag, temp = reader.read()
		print("------ %s ------" % (count))
		print(x.strftime("%x %X"))
		
		user = select_user_data(str(tag))
		
		if not user:
			choice, name = input_user_data()
			
			if choice == True:
				create_new_user(name, str(tag))
			else:
				print("Scanned tag is not associated with any student")
		else:
			update_user_attendance_time(user)
			print("\n")
except:
    GPIO.cleanup()
finally:
	db.close()
	GPIO.cleanup()
