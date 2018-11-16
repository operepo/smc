#!/usr/bin/python
import os
import sys
from getpass import getpass

sys.path.append("/home/www-data/web2py/")

# Move back to the main web2py folder
#print os.getcwd()
os.chdir("/home/www-data/web2py/")
#print os.getcwd()

from gluon.main import save_password

# RUN THIS FROM DOCKER CONTAINER
# TODO - make this pull from preset repository on boot?
# : docker exec -it ope_ope-smc_1 python /home/www-data/web2py/applications/smc/set_admin_password.py 
# or: docker exec -it ope_ope-smc_1 /set_admin_password


password = ""
match = False

#if (len(sys.argv) >=2):
#    password = sys.argv[1]


while (match != True):
	pw = getpass("Please enter new admin password for SMC: ")
	pw2 = getpass("Enter password again to confirm: ")
	
	if (pw != pw2):
		print "\t\tPasswords don't match, try again!!!!"
	else:
		match = True
		password = pw
		
password = password.strip()
if (password != ""):
	save_password(password,80)
	save_password(password,443)
