from fastapi import FastAPI, Request
import psycopg2
import json
import requests
import os
app = FastAPI()

def get_connection():
   return psycopg2.connect(os.getenv("DATABASE_URL"))

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id SERIAL PRIMARY KEY,
            date TEXT,
            time TEXT,
            customer_name TEXT,
            customer_phone TEXT,
            status TEXT DEFAULT 'confirmed'
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ---------- BOOK APPOINTMENT ----------
@app.post("/check-and-book")
async def check_and_book(request: Request):

    body = await request.json()

    print("=" * 50)
    print("RAW BODY (book):", json.dumps(body, indent=2))
    print("=" * 50)

    date = body.get("date")
    time = body.get("Time") or body.get("time")
    customer_name = body.get("customer_name")
    customer_phone = body.get("customer_phone") or body.get("phone")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM bookings WHERE date = %s AND time = %s",
        (date, time)
    )

    existing = cursor.fetchone()

    if existing:

        conn.close()

        result_message = (
            f"Sorry, {date} at {time} is already booked. "
            "Please suggest another time."
        )

    else:

        cursor.execute(
            """
            INSERT INTO bookings
            (date, time, customer_name, customer_phone)
            VALUES (%s, %s, %s, %s)
            """,
            (date, time, customer_name, customer_phone)
        )

        conn.commit()
        conn.close()

        # Send booking information to Make.com
        make_webhook_url = os.getenv("MAKE_WEBHOOK_URL")

        notification_data = {
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "date": date,
            "time": time
        }

        try:

            make_response = requests.post(
                make_webhook_url,
                json=notification_data,
                timeout=10
            )

            print("MAKE RESPONSE:", make_response.status_code)
            print("MAKE BODY:", make_response.text)

        except Exception as e:

            print("MAKE WEBHOOK ERROR:", e)

        result_message = (
            f"Booked successfully for {customer_name} "
            f"on {date} at {time}."
        )

    print(f"RESULT: {result_message}")

    return {
        "result": result_message,
        "success": existing is None
    }


# ---------- CANCEL APPOINTMENT ----------
@app.post("/cancel-booking")
async def cancel_booking(request: Request):

    body = await request.json()

    print("=" * 50)
    print("RAW BODY (cancel):", json.dumps(body, indent=2))
    print("=" * 50)

    date = body.get("date")
    time = body.get("Time") or body.get("time")
    customer_name = body.get("customer_name")
    
    print("DATE:", date)
    print("TIME:", time)
    print("CUSTOMER:", customer_name)

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, date, time, customer_name FROM bookings")
    print("ALL BOOKINGS:", cursor.fetchall())

    cursor.execute(
    """
    SELECT * FROM bookings
    WHERE date = %s AND time = %s AND customer_name = %s
    """,
    (date, time, customer_name)
)
   
    existing = cursor.fetchone()

    if not existing:

        conn.close()

        result_message = (
            f"No booking found for {customer_name} "
            f"on {date} at {time}. "
            "Please double-check the name, date, and time."
        )

    else:

        cursor.execute(
            """
            DELETE FROM bookings
            WHERE date = %s AND time = %s AND customer_name = %s
            """,
            (date, time, customer_name)
        )

        conn.commit()
        conn.close()

        result_message = (
            f"The booking for {customer_name} on {date} at {time} "
            "has been cancelled successfully."
        )

    print(f"RESULT: {result_message}")

    return {
        "result": result_message,
        "success": existing is not None
    }


# ---------- VIEW ALL BOOKINGS ----------
@app.get("/bookings")
def get_all_bookings():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings")

    rows = cursor.fetchall()

    conn.close()

    return {
        "bookings": rows
    }