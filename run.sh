#!/bin/bash

# Activate the virtual environment
source /root/PROJECT-3-K/myenv/bin/activate

# Start alpha-service-2.py on port 9001
export FLASK_APP=alpha-service-2.py
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=9001
flask run &

# Start app-3.py on port 9002
export FLASK_APP=app-3.py
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=9002
flask run &

# Start geo.py on port 9003
export FLASK_APP=geo.py
export FLASK_RUN_HOST=0.0.0.0
export FLASK_RUN_PORT=9003
flask run &
