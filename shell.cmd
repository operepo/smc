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


echo %ESC_GREEN%Removing PYC files...%ESC_RESET%
!PYEXE! clear_pyc_files.py

echo %ESC_GREEN%Starting Web2Py Shell...%ESC_RESET%
!PYEXE! web2py/web2py.py -S smc -M


:eof