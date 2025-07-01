# smc
Student Management Console - Easy student management and enrollment for education institutions. Includes a movie library and integration with Active Directory, Canvas, and WAMAP.

# Requirements
All required packages are listed in modules.txt

# Environment Setup
To build psycopg2 from source in Ubuntu, run the following command
```
sudo apt install postgresql-server-dev-all
```

Create Python virtual enviroment and install Python packages

```
python3 -m venv .venv
pip install -r modules.txt
```

# Run
```
source .venv/bin/activate
./start_smc.sh
```

# Test Cert Files
test.crt and test.key are for development purposes only. Do not use in production.
When bundled with OPE services, these files are ignored

