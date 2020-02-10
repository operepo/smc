@echo off
SETLOCAL ENABLEEXTENSIONS
SETLOCAL ENABLEDELAYEDEXPANSION
rem DISABLEDELAYEDEXPANSION

rem escape code for colors
SET ESC=[
SET ESC_CLEAR=%ESC%2j
SET ESC_RESET=%ESC%0m
SET ESC_GREEN=%ESC%32m
SET ESC_RED=%ESC%31m
SET ESC_YELLOW=%ESC%33m


rem NET FILE 1>NUL 2>NUL

REM Generate test cert
REM git bash here (web2py folder)
REM openssl genrsa -out test.key 2048
REM openssl req -new -key test.key -out test.csr
REM openssl x509 -req -days 3650 -in test.csr -signkey test.key -out test.crt

rem cd server/web2py

REM - Start the virtual env
REM venv\scripts\activate.bat

REM echo Running Python Virtual Env
REM === FIND PYTHON! ===
SET PYEXE=G:\CSE_PORTABLE_CODE\VSCode\WPy32-3680\python-3.6.8\python.exe

echo %ESC_YELLOW%trying python !PYEXE!... %ESC_RESET%
if NOT EXIST !PYEXE! (
    SET PYEXE=c:\python36-32\python.exe
    echo %ESC_YELLOW%trying python !PYEXE!... %ESC_RESET%
)
if NOT EXIST !PYEXE! (
    SET PYEXE=c:\python37-32\python.exe
    echo %ESC_YELLOW%trying python !PYEXE!... %ESC_RESET%
)

rem SET PYEXE=%~dp0venv\scripts\python.exe
rem SET PYEXE=python36.exe

rem echo !PYEXE!
SET LISTEN_IP=127.0.0.1
SET W_SSL=1
SET SSL_CERT="test.crt"
SET SSL_KEY="test.key"


echo %ESC_GREEN%Removing PYC files...%ESC_RESET%
!PYEXE! clear_pyc_files.py

echo %ESC_GREEN%Ensuring Web2Py Admin Password...%ESC_RESET%
!PYEXE! -B web2py/ensure_password.py

rem echo "Make sure to set IT_PW env variable if needed for laptop authentication"
del kill_smc.bat 1>NUL 2>NUL

echo %ESC_RED%============================================
echo %ESC_RED%=== RUN KILL_SMC.BAT to stop the process ===%ESC_RESET%
echo %ESC_RED%============================================%ESC_RESET%
rem echo    (it stores the taskkill command for easy use later)

rem If running standalone - set enc key by setting env variable
rem SET "CANVAS_SECRET=ALFKJOIUXETRKH@&YF(*&Y#$9a78sd:O"


if "%W_SSL%"=="1" (
    rem test
    echo %ESC_GREEN%Starting Web2Py w SSL...%ESC_RESET%
    !PYEXE! -B web2py/web2py.py -p 8000 -i "%LISTEN_IP%" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 -K smc --with-scheduler -a "<recycle>" --no_gui --ssl_certificate=%SSL_CERT% --ssl_private_key=%SSL_KEY% 
    rem  # --ca-cert="ca.crt"
) else (
    echo %ESC_GREEN%Starting Web2Py...%ESC_RESET%
    !PYEXE! -B web2py/web2py.py -p 8000 -i "%LISTEN_IP%" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 -K smc --with-scheduler -a "<recycle>" --no_gui 
)



rem venv\scripts\deactivate.bat

REM PyCharm Settings
REM Parameters: -p 8000 -i "0.0.0.0" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 -K smc --with-scheduler --ssl_certificate="test.crt" --ssl_private_key="test.key" -a "<recycle>"
REM Interpereted Options: -B
