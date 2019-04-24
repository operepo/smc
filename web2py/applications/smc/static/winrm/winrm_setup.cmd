@echo off

rem http://www.hurryupandwait.io/blog/understanding-and-troubleshooting-winrm-connection-and-authentication-a-thrill-seekers-guide-to-adventure

rem Need this to allow other admin accounts to run winrm commands - not just the built in administrator account
call reg add HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System /v LocalAccountTokenFilterPolicy /t REG_DWORD /d 1 /f

rem todo restart the winrm service
call net stop winrm
call net start winrm

call winrm quickconfig -transport:http
call winrm set winrm/config/client/auth @{Basic="true"}
call winrm set winrm/config/service/auth @{Basic="true"}
call winrm set winrm/config/service @{AllowUnencrypted="true"}
echo Make sure your admin account has full control in the next config box!!!
pause
call winrm configSDDL default      



rem possible workarounds?
rem net localgroup WinRMRemoteWMIUsers__ /add \ 


rem Allow winrm through the firewall
rem NOTE - quickconfig command above should do this too
rem netsh advfirewall firewall add rule name="WinRM-HTTP" dir=in localport=5985 protocol=TCP action=allow
rem netsh advfirewall firewall add rule name="WinRM-HTTPS" dir=in localport=5986 protocol=TCP action=allow


rem Generate new self signed cert?
rem $c = New-SelfSignedCertificate -DnsName "<IP or host name>" -CertStoreLocation cert:\LocalMachine\My
