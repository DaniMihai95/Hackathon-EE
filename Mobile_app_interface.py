import os
import time
import random
from datetime import datetime
from dateutil import tz
import requests
import streamlit as st




st.set_page_config(
    page_title="Patient Monitor",
    page_icon="🏥",
    layout="wide"
)

# Dummy credentials
VALID_USERNAME = "admin"
VALID_PASSWORD = "password123"

# Initialize session state for login
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Login page
if not st.session_state.logged_in:
    # Hide everything and show only login
    st.markdown("""
    <style>
    /* Hide default Streamlit elements on login page */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("# 🏥 Patient Monitor")
        st.markdown("### Login")
        
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter username")
            password = st.text_input("Password", type="password", placeholder="Enter password")
            submit = st.form_submit_button("Login", use_container_width=True)
            
            if submit:
                if username == VALID_USERNAME and password == VALID_PASSWORD:
                    st.session_state.logged_in = True
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.info("💡 Demo credentials:\n\nUsername: `admin`\n\nPassword: `password123`")
    
    st.stop()  # Stop execution here if not logged in

# Mock condition variable (should be fetched from API)
cond = "stable"

# Map condition to phase class
phase_class = {
    "critical": "bad",
    "watch": "warn",
    "stable": "good",
    "discharged": "good",
}.get(cond, "warn")

# Function to generate live fluctuating vitals
def generate_vitals():
    # Heart Rate: 68-72 bpm
    hr = random.randint(68, 72)
    
    # SpO2: 96-99%
    spo2 = random.randint(96, 99)
    
    # Temperature: 36.5-37.0°C (fluctuate by ±0.1)
    temp = round(random.uniform(36.5, 37.0), 1)
    
    # Respiratory Rate: 14-18 breaths/min
    resp = random.randint(14, 18)
    
    # Blood Pressure: 115-125 / 75-85
    systolic = random.randint(115, 125)
    diastolic = random.randint(75, 85)
    bp = f"{systolic}/{diastolic}"
    
    return {
        "HR": str(hr),
        "SpO2": str(spo2),
        "Temp": str(temp),
        "Resp": str(resp),
        "BP": bp
    }

# Helper function for local time
def _local_t(iso_str):
    if not iso_str:
        return ""
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.astimezone(tz.tzlocal()).strftime("%Y-%m-%d %H:%M:%S")
    except:
        return iso_str

# Initialize session state for previous values
if 'prev_vitals' not in st.session_state:
    st.session_state.prev_vitals = None

# Placeholder for dynamic content that updates
placeholder = st.empty()

# Continuous loop for live updates
while True:
    # Generate fresh vitals on every iteration for real-time updates
    current_vitals = generate_vitals()
    
    # Calculate deltas (changes from previous values)
    deltas = {}
    if st.session_state.prev_vitals:
        try:
            deltas['HR'] = int(current_vitals['HR']) - int(st.session_state.prev_vitals['HR'])
            deltas['SpO2'] = int(current_vitals['SpO2']) - int(st.session_state.prev_vitals['SpO2'])
            deltas['Temp'] = round(float(current_vitals['Temp']) - float(st.session_state.prev_vitals['Temp']), 1)
            deltas['Resp'] = int(current_vitals['Resp']) - int(st.session_state.prev_vitals['Resp'])
            # For BP, we'll track systolic only
            current_sys = int(current_vitals['BP'].split('/')[0])
            prev_sys = int(st.session_state.prev_vitals['BP'].split('/')[0])
            deltas['BP'] = current_sys - prev_sys
        except:
            deltas = {}
    
    # Update previous vitals for next iteration
    st.session_state.prev_vitals = current_vitals.copy()
    
    status = {
        "patient": {"name": "Patient Name"},
        "summary": "Patient is in stable condition",
        "last_update": datetime.now().isoformat(),
        "vitals": current_vitals,
        "feed": []
    }
    
    with placeholder.container():
        c1, c2 = st.columns([1, 2], gap="large")

        with c1:
            st.markdown(f"<div class='card {phase_class}'>", unsafe_allow_html=True)
            st.subheader(f"{status['patient']['name']}")
            st.write(f"**Condition:** `{cond.upper()}`")
            st.write(status.get("summary", ""))
            st.write(f"<span class='muted'>Last update: {_local_t(status.get('last_update',''))}</span>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("#### Vitals")
            vit = status.get("vitals", {})
            m1, m2, m3 = st.columns(3)
            m1.metric("Heart rate", f"{vit.get('HR','–')} bpm", delta=deltas.get('HR', None), delta_color="off")
            m2.metric("SpO₂", f"{vit.get('SpO2','–')}%", delta=deltas.get('SpO2', None), delta_color="off")
            m3.metric("Temperature", f"{vit.get('Temp','–')}°C", delta=deltas.get('Temp', None), delta_color="off")
            m4, m5 = st.columns(2)
            m4.metric("Respiratory rate", f"{vit.get('Resp','–')}/min", delta=deltas.get('Resp', None), delta_color="off")
            m5.metric("Blood pressure", f"{vit.get('BP','–')}", delta=deltas.get('BP', None), delta_color="off")
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("#### Care Team Updates")
            feed = status.get("feed", [])
            if not feed:
                st.write("No updates yet.")
            else:
                for item in feed:
                    with st.container():
                        st.write(f"**{_local_t(item.get('ts',''))}** — {item.get('text','')}")
            st.markdown("<hr>", unsafe_allow_html=True)
            st.caption("These updates are informational only. For urgent questions, contact the care team directly.")
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Wait 5 second before next update
    time.sleep(5)