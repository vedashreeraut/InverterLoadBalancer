import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

app = FastAPI()
DB="data.db"
CAP=800

def db():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    return c

@app.on_event("startup")
def start():
    c=db()
    c.execute("""CREATE TABLE IF NOT EXISTS a (
        id INTEGER PRIMARY KEY, name TEXT, watt INTEGER,
        priority INTEGER, status TEXT)""")
    c.commit()
    c.close()

def all():
    c=db()
    x= c.execute("SELECT * FROM a ORDER BY priority").fetchall()
    c.close()
    return [dict(i) for i in x]

def load():
    c=db()
    x= c.execute(
        "SELECT COALESCE(SUM(watt), 0) FROM a WHERE status='on'").fetchone()[0]
    c.close()
    return x

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/api")
def get():
    return {"capacity": CAP(), "load": load(), "appliances": all()}

@app.post("/api")
def add(x:dict):
    if not x.get("name") or not x.get("watt",0) <= 0 or x.get("priority",0)<=0:
        raise HTTPException(400, "Invalid appliance")
    c=db()
    c.execute("INSERT INTO a (name, watt, priority, status) VALUES (?, ?, ?, 'off')",
              (x["name"], x["watt"], x["priority"]))
    c.commit()
    c.close()
    return {"message": "Added"}

@app.delete("/api/{id}")
def delete(id:int):
    c=db()
    c.execute("DELETE FROM a WHERE id=?", (id,))
    c.commit()
    c.close()
    restore()
    return {"message": "Deleted"}

def restore():
    c=db()
    used=c.execute(
        "SELECT COALESCE(SUM(watt), 0) FROM a WHERE state='on'").fetchone()[0]
    rows = c.execute(
        "SELECT * FROM a WHERE state='shed' ORDER BY priority.id").fetchall()
    for r in rows:
        if used + r["watt"] <= CAP:
            c.execute("UPDATE a SET state='on' WHERE id=?", (r["id"],))
            used += r["watt"]
    c.commit()
    c.close()
    
@app.post("/api/{id}/on")
def on(id:int):
    c=db()
    r=c.execute("SELECT * FROM a WHERE id=?", (id,)).fetchone()
    if not r:
        c.close()
        raise HTTPException(404, "Not found")
    if r["state"]=="on":
        c.close()
        raise HTTPException(400, "Already on")
    used=c.execute(
        "SELECT COALESCE(SUM(watt), 0) FROM a WHERE state='on'").fetchone()[0]
    need=used + r["watt"]
    shed=[]
    rows=c.execute(
        """SELECT * FROM a 
        WHERE state='on' ORDER BY priority>?
        ORDER BY priority DESC, id DESC
        """,(r["priority"],)).fetchall()
    for x in rows:
        if need <= CAP:
            break
        c.execute("UPDATE a SET state='shed' WHERE id=?", (x["id"],))
        need -= x["watt"]
        shed.append(x["name"])
    if need>CAP:
        for x in rows:
            c.execute("UPDATE a SET state='on' WHERE id=?", (x["id"],))
        c.commit()
        c.close()
        raise HTTPException(409, "Rejected: not enough capacity")
    c.execute("UPDATE a SET state='on' WHERE id=?", (id,))
    c.commit()
    c.close()
    return{"message":"ON"+(" | Shed: "+", ".join(shed) if shed else "")}

@app.post("/api/{id}/off")
def off(id:int):
    c=db()
    r=c.execute("SELECT * FROM a WHERE id=?", (id,)).fetchone()
    if not r:
        c.close()
        raise HTTPException(404, "Not found")
    c.execute("UPDATE a SET state='off' WHERE id=?", (id,))
    c.commit()
    c.close()
    restore()
    return {"message": "OFF"}