
rem cd server/web2py

python2 clear_pyc_files.py

python2 -B web2py/ensure_password.py

rem echo "Make sure to set IT_PW env variable if needed for laptop authentication"

python2 -B web2py/web2py.py -p 8000 -i "0.0.0.0" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 -K smc --with-scheduler --ssl_certificate="test.crt" --ssl_private_key="test.key" -a "<recycle>"
rem  # --ca-cert="ca.crt" --nogui 
