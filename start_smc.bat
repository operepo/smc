
REM Generate test cert
REM git bash here (web2py folder)
REM openssl genrsa -out test.key 2048
REM openssl req -new -key test.key -out test.csr
REM openssl x509 -req -days 3650 -in test.csr -signkey test.key -out test.crt

rem cd server/web2py

python2 clear_pyc_files.py

python2 -B web2py/ensure_password.py

rem echo "Make sure to set IT_PW env variable if needed for laptop authentication"

python2 -B web2py/web2py.py -p 8000 -i "0.0.0.0" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 -K smc --with-scheduler --ssl_certificate="test.crt" --ssl_private_key="test.key" -a "<recycle>"
rem  # --ca-cert="ca.crt" --nogui 


REM PyCharm Settings
REM Parameters: -p 8000 -i "0.0.0.0" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 -K smc --with-scheduler --ssl_certificate="test.crt" --ssl_private_key="test.key" -a "<recycle>"
REM Interpereted Options: -B