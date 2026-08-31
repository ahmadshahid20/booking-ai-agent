from fastapi import FastAPI, Request
import sqlite3
import json
from pydantic import BaseModel

app = FastAPI()

def init_db():
    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            time TEXT,
            customer_name TEXT,
            status TEXT DEFAULT 'confirmed'
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.post("/check-and-book")
async def check_and_book(request: Request):
    body = await request.json()

    print("=" * 50)
    print("RAW BODY RECEIVED FROM VAPI:")
    print(json.dumps(body, indent=2))
    print("=" * 50)

    # Vapi's "API Request" tool sends parameters directly (flat), not wrapped.
    # Key might be "Time" or "time" depending on how the parameter was named.
    date = body.get("date")
    time = body.get("Time") or body.get("time")
    customer_name = body.get("customer_name")

    print(f"PARSED -> date={date}, time={time}, customer_name={customer_name}")

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings WHERE date = ? AND time = ?", (date, time))
    existing = cursor.fetchone()

    if existing:
        conn.close()
        result_message = f"Sorry, {date} at {time} is already booked. Please suggest another time."
    else:
        cursor.execute(
            "INSERT INTO bookings (date, time, customer_name) VALUES (?, ?, ?)",
            (date, time, customer_name)
        )
        conn.commit()
        conn.close()
        result_message = f"Booked successfully for {customer_name} on {date} at {time}."

    print(f"RESULT: {result_message}")

    # Return plain JSON - Vapi's API Request tool reads this directly
    return {"result": result_message, "success": existing is None}

@app.get("/bookings")
def get_all_bookings():
    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bookings")
    rows = cursor.fetchall()
    conn.close()
    return {"bookings": rows}

#Cancel Appointment

class CancelBookingRequest(BaseModel):
    date: str
    time: str
    customer_name: str


@app.post("/cancel-booking")
async def cancel_booking(data: CancelBookingRequest):

    date = data.date
    time = data.time
    customer_name = data.customer_name

    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

   
    cursor.execute("SELECT * FROM bookings")
    all_bookings = cursor.fetchall()
    
    print("ALL BOOKINGS:", all_bookings)
    
    cursor.execute(
        "SELECT * FROM bookings WHERE date = ? AND time = ? AND customer_name = ?",
        (date, time, customer_name)
    )

    existing = cursor.fetchone()

    if not existing:
        conn.close()

        return {
            "result": f"No booking found for {customer_name} on {date} at {time}.",
            "success": False
        }

    cursor.execute(
        "DELETE FROM bookings WHERE date = ? AND time = ? AND customer_name = ?",
        (date, time, customer_name)
    )

    conn.commit()
    conn.close()
   
    return {
        "result": f"The booking for {customer_name} on {date} at {time} has been cancelled successfully.",
        "success": True
    }
    
   