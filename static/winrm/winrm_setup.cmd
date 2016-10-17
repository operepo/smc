@echo off

call winrm quickconfig -transport:http
call winrm set winrm/config/client/auth @{Basic="true"}
call winrm set winrm/config/service/auth @{Basic="true"}
call winrm set winrm/config/service @{AllowUnencrypted="true"}
call winrm configSDDL default      

