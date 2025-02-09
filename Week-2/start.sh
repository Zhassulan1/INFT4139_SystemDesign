~Desktop/SystemDesign/Week-2/env1/bin/uvicorn main:app --workers 5 --loop uvloop --port 8001 --http httptools --log-level error & \
~Desktop/SystemDesign/Week-2/env2/bin/uvicorn main:app --workers 5 --loop uvloop --port 8002 --http httptools --log-level error & \
~Desktop/SystemDesign/Week-2/env3/bin/uvicorn main:app --workers 5 --loop uvloop --port 8003 --http httptools --log-level error & \
