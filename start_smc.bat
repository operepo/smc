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


REM Generate test cert
SET SSL_KEY=web2py/test.key
SET SSL_CRT=web2py/test.crt
SET SSL_CSR=web2py/test.csr
if not exist %SSL_CRT% (
    echo %ESC_GREEN%Generating test ssl cert...%ESC_RESET%
    openssl genrsa -out %SSL_KEY% 2048
    openssl req -new -key %SSL_KEY% -out %SSL_CSR%
    openssl x509 -req -days 3650 -in %SSL_CSR% -signkey %SSL_KEY% -out %SSL_CRT%
)


REM === FIND PYTHON! ===
SET PYEXE=python.exe

echo %ESC_GREEN%Searching for python...%ESC_RESET%
for %%g in (
        g:\CSE_PORTABLE_CODE\VSCode\WPy32-3680\python-3.6.8\python.exe
        d:\CSE_PORTABLE_CODE\VSCode\WPy32-3680\python-3.6.8\python.exe
        c:\python36-32\python.exe
        c:\python37-32\python.exe
    ) do (
        if exist %%g (
            SET PYEXE=%%g
            echo %ESC_YELLOW%Found python at: !PYEXE!... %ESC_RESET%
            goto :for_loop_done
        )
    )

:for_loop_done

SET LISTEN_IP=127.0.0.1
SET W_SSL=1
SET SSL_CERT="test.crt"
SET SSL_KEY="test.key"
SET W_SCHEDULER=-K smc --with-scheduler
rem -K smc --with-scheduler


echo %ESC_GREEN%Removing PYC files...%ESC_RESET%
!PYEXE! clear_pyc_files.py

echo %ESC_GREEN%Ensuring Web2Py Admin Password...%ESC_RESET%
!PYEXE! -B web2py/ensure_password.py

rem Remove prev kill bat file as it will get rewritten
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
    !PYEXE! -B web2py/web2py.py -p 8000 -i "%LISTEN_IP%" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 %W_SCHEDULER% -a "<recycle>" --no_gui --ssl_certificate=%SSL_CERT% --ssl_private_key=%SSL_KEY% 
    rem  # --ca-cert="ca.crt"
) else (
    echo %ESC_GREEN%Starting Web2Py...%ESC_RESET%
    !PYEXE! -B web2py/web2py.py -p 8000 -i "%LISTEN_IP%" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 %W_SCHEDULER% -a "<recycle>" --no_gui 
)


:eof