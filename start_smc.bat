@echo off

REM Generate test cert
REM git bash here (web2py folder)
REM openssl genrsa -out test.key 2048
REM openssl req -new -key test.key -out test.csr
REM openssl x509 -req -days 3650 -in test.csr -signkey test.key -out test.crt

rem cd server/web2py

REM - Start the virtual env
REM venv\scripts\activate.bat

REM echo Running Python Virtual Env
rem SET PYEXE=%~dp0venv\scripts\python.exe
SET PYEXE=python36.exe
rem echo %PYEXE%



echo [32mRemoving PYC files...[0m
%PYEXE% clear_pyc_files.py

echo [32mEnsuring Web2Py Admin Password...[0m
%PYEXE% -B web2py/ensure_password.py

rem echo "Make sure to set IT_PW env variable if needed for laptop authentication"
del kill_smc.bat

echo .
echo .
echo [31m=== RUN KILL_SMC.BAT to stop the process ===[0m
echo    (it stores the taskkill command for easy use later)
echo .
echo .

rem If running standalone - set enc key by setting env variable
rem SET "CANVAS_SECRET=ALFKJOIUXETRKH@&YF(*&Y#$9a78sd:O"

echo [32mStarting Web2Py...[0m
%PYEXE% -B web2py/web2py.py -p 8000 -i "0.0.0.0" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 -K smc --with-scheduler 
rem --ssl_certificate="test.crt" --ssl_private_key="test.key" -a "<recycle>"
rem  # --ca-cert="ca.crt" --nogui 

rem venv\scripts\deactivate.bat

REM PyCharm Settings
REM Parameters: -p 8000 -i "0.0.0.0" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 -K smc --with-scheduler --ssl_certificate="test.crt" --ssl_private_key="test.key" -a "<recycle>"
REM Interpereted Options: -B
