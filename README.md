INVERTER LOAD BALANCER
A web-based inverter load management system built using FastAPI, SQLite, HTML, CSS and JavaScript.

Features:
1. Add and manage appliances with wattage and priotity.
2. Turn appliances On/Off
3. Automatically shed lower-priority appliances when capacity is exceeded.
4. Restore appliances when sufficient capacity becomes available
5. Displays current inverter load ad appliance states
6. Includes Turn Everythin OFF controls.

Run:
pip install -r requirements.txt
uvicorn main:app --reload

Open:
http://127.0.0.1:8000

Priority Rule:
Priority 1 - highest priority
When capacity is insufficient, lower-priority appliances are shed first.