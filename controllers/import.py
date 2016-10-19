# coding: utf8
from ednet.util import Util
from ednet.ad import AD
from ednet.student import Student
from ednet.faculty import Faculty

import os

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def index(): return dict(message="hello from import.py")


def start_create_home_directory():
	# Start the worker process
	cmd = "/usr/bin/nohup /usr/bin/python " + os.path.join(request.folder, 'static/scheduler/start_create_home_directory_scheduler.py') + " > /dev/null 2>&1 &"
	p = subprocess.Popen(cmd, shell=True, close_fds=True)
	ret = ""
	#ret = p.wait()
	#ret = p.communicate()[0]
	#p.wait()
	#time.sleep(2)
	#p.kill()
	#ret = ""
	return ret


def start_process_queue():
	return start_create_home_directory()


@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def student_pick_excel():
	f = None
	excel_output = None
	form = SQLFORM(db.student_excel_uploads).process()
	if form.accepted:
		#session.flash = "Processing File."
		f = form.vars.excel_file
		redirect(URL('student_show_excel_contents', vars=dict(excel_file=f)))
	elif form.errors:
		response.flash = "Form Errors"
	else:
		response.flash = "Upload Excel file or choose previous import."
	return dict(form=form, file_name=f, out=excel_output)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def student_pick_excel_prev_workbooks():
	delete_id = request.vars.delete_id
	if (delete_id != None):
		# Delete id was passed, remove it
		db(db.student_excel_uploads.id==delete_id).delete()
		# This should remove uploaded file too
	rows = db(db.student_excel_uploads).select(orderby=~db.student_excel_uploads.created_on)
	return dict(rows=rows)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def student_show_excel_contents():
	excel_file = request.vars.excel_file
	return locals()

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def student_show_excel_contents_process():
	# Process the files...
	excel_file = request.vars.excel_file
	f = os.path.join(request.folder,'uploads',excel_file)
	excel_output = Student.ProcessExcelFile(f)
	response.js = "ImportComplete();"
	return excel_output

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def student_show_excel_contents_sheet_dropdown():
	o = [OPTION(cat.sheet_name, _value=cat.sheet_name) for cat in db().select(db.student_import_queue.sheet_name, groupby=db.student_import_queue.sheet_name)]
	s = SELECT(o, _id='pick_sheet', _onchange="SheetChanged();")
	response.js = "SheetChanged();"
	
	erase_current_password = INPUT(_type='checkbox', _name='erase_current_password', _id='erase_current_password', _value="False", _onclick='if ($("#erase_current_password").val() == "True") { $("#erase_current_password").val("False"); } else { $("#erase_current_password ").val("True"); }')
	
	erase_current_quota = INPUT(_type='checkbox', _name='erase_current_quota', _id='erase_current_quota', _value="False", _onclick='if ($("#erase_current_quota").val() == "True") { $("#erase_current_quota").val("False"); } else { $("#erase_current_quota").val("True"); }')
	
	go = INPUT(_type='button', _name='go', _value='Import Sheet', _onclick='StartImport();')
	return dict(dropdown=s, erase_current_password=erase_current_password, erase_current_quota=erase_current_quota, go_button=go)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def student_show_excel_contents_sheet_grid():
	sheet_name = request.vars.sheet_name
	query = (db.student_import_queue.sheet_name==sheet_name)
	#rows = db(query).select()
	g = SQLFORM.grid(query,editable=False, create=False, deletable=False,csv=False,links=False,links_in_grid=False,details=False,searchable=False,orderby=[~db.student_import_queue.account_enabled,db.student_import_queue.user_id])
	response.js = "ColorDisabledRows();"
	return g

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def student_do_import():
	AD.Close()
	
	sheet_name = request.vars.sheet_name
	erase_current_password = False
	if (request.vars.erase_current_password == "True"):
		erase_current_password = True
	erase_current_quota = False
	if (request.vars.erase_current_quota == "True"):
		erase_current_quota = True
	
	# Add student account to student_info table
	count = Student.CreateW2PyAccounts(sheet_name, erase_current_password, erase_current_quota)
	
	# Setup queue for canvas and for ad imports
	count2 = Student.QueueActiveDirectoryImports(sheet_name)
	count2 = Student.QueueCanvasImports(sheet_name)
	if (count2 > count):
		count = count2
	
	return dict(sheet_name=sheet_name, count=count)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def student_do_import_ad():
	session.forget(response) # Don't need the session so don't block on it
	#session._unlock(response)
	# Pop off the list an item and process it
	result = Student.ProcessADStudent()
	
	# Make it call us again until we are done
	response.js = "ImportAD();"
	
	# Make sure the scheduler is running
	start_process_queue()
	return result

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def student_do_import_canvas():
	session.forget(response) # Don't need the session so don't block on it
	#session._unlock(response)
	# Pop off the list an item and process it
	result = Student.ProcessCanvasStudent()
	
	# Make it call us again until we are done
	response.js = "ImportCanvas();"
	
	# Make sure the scheduler is running
	start_process_queue()
	return result
	


#######################
# Faculty Functions

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_pick_excel():
	f = None
	excel_output = None
	form = SQLFORM(db.faculty_excel_uploads).process()
	if form.accepted:
		#session.flash = "Processing File."
		f = form.vars.excel_file
		redirect(URL('faculty_show_excel_contents', vars=dict(excel_file=f)))
	elif form.errors:
		response.flash = "Form Errors"
	else:
		response.flash = "Upload Excel file or choose previous import."
	return dict(form=form, file_name=f, out=excel_output)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_pick_excel_prev_workbooks():
	delete_id = request.vars.delete_id
	if (delete_id != None):
		# Delete id was passed, remove it
		db(db.faculty_excel_uploads.id==delete_id).delete()
		# This should remove uploaded file too
	rows = db(db.faculty_excel_uploads).select(orderby=~db.faculty_excel_uploads.created_on)
	return dict(rows=rows)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_show_excel_contents():
	excel_file = request.vars.excel_file
	return locals()

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_show_excel_contents_process():
	# Process the files...
	excel_file = request.vars.excel_file
	f = os.path.join(request.folder,'uploads',excel_file)
	excel_output = Faculty.ProcessExcelFile(f)
	response.js = "ImportComplete();"
	return excel_output

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_show_excel_contents_sheet_dropdown():
	o = [OPTION(cat.sheet_name, _value=cat.sheet_name) for cat in db().select(db.faculty_import_queue.sheet_name, groupby=db.faculty_import_queue.sheet_name)]
	s = SELECT(o, _id='pick_sheet', _onchange="SheetChanged();")
	response.js = "SheetChanged();"
	
	erase_current_password = INPUT(_type='checkbox', _name='erase_current_password', _id='erase_current_password', _value="False", _onclick='if ($("#erase_current_password").val() == "True") { $("#erase_current_password").val("False"); } else { $("#erase_current_password ").val("True"); }')
	
	erase_current_quota = INPUT(_type='checkbox', _name='erase_current_quota', _id='erase_current_quota', _value="False", _onclick='if ($("#erase_current_quota").val() == "True") { $("#erase_current_quota").val("False"); } else { $("#erase_current_quota").val("True"); }')
	
	go = INPUT(_type='button', _name='go', _value='Import Sheet', _onclick='StartImport();')
	return dict(dropdown=s, erase_current_password=erase_current_password, erase_current_quota=erase_current_quota, go_button=go)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_show_excel_contents_sheet_grid():
	sheet_name = request.vars.sheet_name
	query = (db.faculty_import_queue.sheet_name==sheet_name)
	#rows = db(query).select()
	g = SQLFORM.grid(query,editable=False, create=False, deletable=False,csv=False,links=False,links_in_grid=False,details=False,searchable=False,orderby=[~db.faculty_import_queue.account_enabled,db.faculty_import_queue.user_id])
	response.js = "ColorDisabledRows();"
	return g

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_do_import():
	AD.Close()
	sheet_name = request.vars.sheet_name
	erase_current_password = False
	if (request.vars.erase_current_password == "True"):
		erase_current_password = True
	erase_current_quota = False
	if (request.vars.erase_current_quota == "True"):
		erase_current_quota = True
	
	# Add faculty account to faculty_info table
	count = Faculty.CreateW2PyAccounts(sheet_name, erase_current_password, erase_current_quota)
	
	# Setup queue for canvas and for ad imports
	count2 = Faculty.QueueActiveDirectoryImports(sheet_name)
	count2 = Faculty.QueueCanvasImports(sheet_name)
	if (count2 > count):
		count = count2
	return dict(sheet_name=sheet_name, count=count)

@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_do_import_ad():
	#session.forget(response) # Don't need the session so don't block on it
	# Pop off the list an item and process it
	result = Faculty.ProcessADFaculty()
	
	# Make it call us again until we are done
	response.js = "ImportAD();"
	
	# Make sure the scheduler is running
	start_process_queue()
	return result
	
@auth.requires(auth.has_membership('Import') or auth.has_membership('Administrators'))
def faculty_do_import_canvas():
	#session.forget(response) # Don't need the session so don't block on it
	# Pop off the list an item and process it
	result = Faculty.ProcessCanvasFaculty()
	
	# Make it call us again until we are done
	response.js = "ImportCanvas();"
	
	# Make sure the scheduler is running
	start_process_queue()
	return result
