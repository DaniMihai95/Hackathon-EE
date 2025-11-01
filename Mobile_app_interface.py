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

# Placeholder for dynamic content that updates
placeholder = st.empty()

# Continuous loop for live updates
while True:
    # Generate fresh vitals on every iteration for real-time updates
    status = {
        "patient": {"name": "Patient Name"},
        "summary": "Patient is in stable condition",
        "last_update": datetime.now().isoformat(),
        "vitals": generate_vitals(),  # Generate NEW values each time
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
            m1.metric("Heart rate", f"{vit.get('HR','–')}", "bpm")
            m2.metric("SpO₂", f"{vit.get('SpO2','–')}", "%")
            m3.metric("Temperature", f"{vit.get('Temp','–')}°C")
            m4, m5 = st.columns(2)
            m4.metric("Respiratory rate", f"{vit.get('Resp','–')}/min")
            m5.metric("Blood pressure", f"{vit.get('BP','–')}")
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