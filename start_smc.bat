
rem cd server/web2py

python web2py/web2py.py -p 8000 -i "0.0.0.0" -e  -s "SMC Server" --minthreads=4 --maxthreads=8 --timeout=60 -K smc --with-scheduler --ssl_certificate="test.crt" --ssl_private_key="test.key"
rem  # --ca-cert="ca.crt" --nogui -a "<recycle>"
