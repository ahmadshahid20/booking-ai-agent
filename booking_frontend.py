import streamlit as st
import requests

# FastAPI URL
API_URL = "https://booking-ai-agent-production.up.railway.app"

st.set_page_config(
    page_title="Booking Dashboard",
    page_icon="📅",
    layout="wide"
)

st.title("📅 Booking Dashboard")
st.write("Manage all your appointments in one place.")

st.divider()

# Get bookings from FastAPI
try:
    response = requests.get(f"{API_URL}/bookings")

    if response.status_code == 200:
        data = response.json()
        bookings = data.get("bookings", [])

        st.subheader("📋 All Bookings")

        if not bookings:
            st.info("No bookings found.")

        else:
            for booking in bookings:

                booking_id = booking[0]
                date = booking[1]
                time = booking[2]
                customer_name = booking[3]
                status = booking[5]

                with st.container(border=True):

                    col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

                    with col1:
                        st.write("👤 **Customer**")
                        st.write(customer_name)

                    with col2:
                        st.write("📅 **Date**")
                        st.write(date)

                    with col3:
                        st.write("🕐 **Time**")
                        st.write(time)

                    with col4:
                        st.write("🟢 **Status**")
                        st.write(status)

                    if st.button(
                        "❌ Cancel Booking",
                        key=f"cancel_{booking_id}"
                    ):

                        cancel_data = {
                            "date": date,
                            "time": time,
                            "customer_name": customer_name
                        }

                        cancel_response = requests.post(
                            f"{API_URL}/cancel-booking",
                            json=cancel_data
                        )

                        if cancel_response.status_code == 200:

                            result = cancel_response.json()

                            if result.get("success"):
                                st.success("Booking cancelled successfully.")
                                st.rerun()
                            else:
                                st.error(result.get("result"))

                        else:
                            st.error("Unable to cancel booking.")

except requests.exceptions.ConnectionError:

    st.error(
        "❌ FastAPI server is not running. "
        "Please start your FastAPI server first."
    )