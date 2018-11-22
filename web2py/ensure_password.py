
import os
import sys
import getpass




curr_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(curr_dir)

from gluon.main import save_password

param_file = os.path.join(curr_dir, "parameters_8000.py")

print(param_file)
if os.path.exists(param_file) is True:
	print("PW already set")
	sys.exit()

pw = getpass.getpass("Enter w2py admin password: ")

save_password(pw, 8000)
