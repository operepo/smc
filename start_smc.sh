#!/bin/bash
# escape code for colors
export ESC=[
export ESC_CLEAR=${ESC}2j
export ESC_RESET=${ESC}0m
export ESC_GREEN=${ESC}32m
export ESC_RED=${ESC}31m
export ESC_YELLOW=${ESC}33m


# Generate test cert
export SSL_KEY=web2py/test.key
export SSL_CRT=web2py/test.crt
export SSL_CSR=web2py/test.csr
if [ ! -f $SSL_CRT ]; then
    echo ${ESC_GREEN}Generating test ssl cert...${ESC_RESET}
    openssl genrsa -out $SSL_KEY 2048
    openssl req -new -key $SSL_KEY -out $SSL_CSR
    openssl x509 -req -days 3650 -in $SSL_CSR -signkey $SSL_KEY -out $SSL_CRT
fi


# === FIND PYTHON! ===
export PYEXE=/usr/bin/python3

echo ${ESC_GREEN}Searching for python...${ESC_RESET}
PythonPaths=(
    "/usr/bin/python3"
)
for g in "${PythonPaths[@]}"; 
do
        if [ -f $g ]; then
            export PYEXE=$g
            echo ${ESC_YELLOW}Found python at: $PYEXE... ${ESC_RESET}
            break
        fi
done


# export LISTEN_IP=127.0.0.1
#export LISTEN_IP=0.0.0.0
export LISTEN_IP="::"
export W_SSL=1
export SSL_CERT="test.crt"
export SSL_KEY="test.key"
export W_SCHEDULER="-K smc --with-scheduler"
# -K smc --with-scheduler


echo ${ESC_GREEN}Removing PYC files...${ESC_RESET}
$PYEXE clear_pyc_files.py

echo ${ESC_GREEN}Ensuring Web2Py Admin Password...${ESC_RESET}
# !PYEXE! -B web2py/ensure_password.py
$PYEXE -B web2py/ensure_password.py

# Remove prev kill bat file as it will get rewritten
rm -f kill_smc.bat

#echo %ESC_RED%============================================
#echo %ESC_RED%=== RUN KILL_SMC.BAT to stop the process ===%ESC_RESET%
#echo %ESC_RED%============================================%ESC_RESET%
#rem echo    (it stores the taskkill command for easy use later)

# If running standalone - set enc key by setting env variable
#export "CANVAS_SECRET=ALFKJOIUXETRKH@&YF(*&Y#$9a78sd:O"

# DEV PORT
DEV_PORT=7999

if [ "$W_SSL" == "1" ]; then
    # test
    echo ${ESC_GREEN}Starting Web2Py w SSL...${ESC_RESET}
    $PYEXE -B web2py/web2py.py -p $DEV_PORT -i "$LISTEN_IP" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 $W_SCHEDULER -a "<recycle>" --no_gui --ssl_certificate=${SSL_CERT} --ssl_private_key=${SSL_KEY}
    # --ca-cert="ca.crt"
else
    echo ${ESC_GREEN}Starting Web2Py...${ESC_RESET}
    $PYEXE -B web2py/web2py.py -p $DEV_PORT -i "${LISTEN_IP}" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 $W_SCHEDULER -a "<recycle>" --no_gui
fi


#:eof