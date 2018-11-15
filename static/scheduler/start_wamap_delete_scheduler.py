#!/usr/bin/python
import sys, os
import subprocess

# Scheduler run by supervisor - do not need to run it manually anymore
sys.exit(0)

# Get the current folder
folder = os.path.abspath(__file__)
folder = os.path.dirname(folder)

# Change to static folder
folder = os.path.dirname(folder)
# Change to app folder
folder = os.path.dirname(folder)
# Get app name
app_name = folder.split(os.sep)[-1]
# Change to applications folder
folder = os.path.dirname(folder)
# Change to w2py root folder
folder = os.path.dirname(folder)

# Set the system to that folder
os.chdir(folder)
# Change to the web2py folder

print "App: " + app_name
print "W2PyFolder: "  + os.getcwd()
group_name = "wamap_delete"
print "Scheduler Group: " + group_name

pid = "0"
try:
	f = open(app_name + ".scheduler." + group_name + ".pid", 'r+')
	pid = f.read()
	f.close()
except IOError:
	pid = "0"
pid = pid.strip()
if (pid == ""):
	pid = "0"
print "Last PID: " + str(pid)

# See if web2py scheduler is running
cmd1 = ["/bin/ps ax | grep 'web2py' | awk '{print $1;}'"]
p1 = subprocess.Popen(cmd1, stdout=subprocess.PIPE, shell=True)
out = p1.communicate()[0]

running = False
for line in out.split(os.linesep):
	if (pid == line.strip()):
		running = True	

print "PS List: " + out

s = open(app_name + '.scheduler.' + group_name + '.log', 'a')
if (running == True):
	# Process is running?
	print "PS IS RUNNING"
	s.write("PS IS RUNNING\n")
else:
	print "PS NOT RUNNING"
	s.write("PS NOT RUNNING\n")
	# Start the scheduler app
	#cmd = ["/usr/bin/nohup /usr/bin/python web2py.py -K " + app_name + " > /dev/null 2>&1 &"]
	cmd = ["/usr/bin/nohup", "/usr/bin/python", "web2py.py", "-K", "'" + app_name + ":" + group_name + "'"] #, "&"] # "> /dev/null 2>&1 &"]
	print "RUN APP: " + str(cmd)
	#p = subprocess.Popen(cmd, shell=True, close_fds=True) #, creationflags=0x00000008)
	p = subprocess.Popen(cmd, close_fds=True) #, creationflags=0x00000008)
	
	f = open(app_name + '.scheduler.' + group_name + '.pid', 'w')
	f.write(str(p.pid))
	f.close()
	# Should run and block until done
	#print p.communicate()[0]
	#p.wait()
s.close()
sys.exit(0)
