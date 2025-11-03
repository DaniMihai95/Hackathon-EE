import os
import time
import random
import json
import glob
import ssl
import uuid
from datetime import datetime
from dateutil import tz
import requests
import streamlit as st
import paho.mqtt.client as mqtt


# MQTT Functions
def _mqtt_client():
    """Connect once and reuse the client from session_state."""
    if "mqtt_client" in st.session_state:
        return st.session_state["mqtt_client"]

    # Use the custom MQTT broker from screenshot
    host = "77.172.166.178"
    port = 51234

    # Create client with unique ID
    client = mqtt.Client(client_id=f"st-pub-{uuid.uuid4()}", clean_session=True)

    # Connection callback
    def on_connect(c, u, flags, rc):
        st.session_state["mqtt_connected"] = (rc == 0)
        if rc == 0:
            st.session_state["mqtt_status"] = "Connected"
        else:
            st.session_state["mqtt_status"] = f"Connection failed: {rc}"
    
    client.on_connect = on_connect

    # Connect to broker
    try:
        client.connect(host, port, keepalive=60)
        client.loop_start()
        
        # Wait for connection
        for _ in range(30):
            if st.session_state.get("mqtt_connected"):
                break
            time.sleep(0.1)
    except Exception as e:
        st.session_state["mqtt_status"] = f"Connection error: {e}"
        return None

    st.session_state["mqtt_client"] = client
    return client

def publish_doctor_message(patient_id: str, text: str):
    """Publish message to hackathon/patient1/bpm topic."""
    # Use the topic format from screenshot: hackathon/patient1
    topic = f"hackathon/{patient_id}"
    
    # Create payload as JSON
    payload = {
        "patient_id": patient_id,
        "role": "doctor",
        "text": text,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    c = _mqtt_client()
    if c is None:
        return None
    
    # Publish with QoS 0 (fire and forget)
    info = c.publish(topic, json.dumps(payload), qos=0, retain=False)
    return info


st.set_page_config(
    page_title="Patient Monitor",
    page_icon="🏥",
    layout="wide"
)

# Dummy credentials
VALID_USERNAME = "admin"
VALID_PASSWORD = "password123"

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'selected_patient' not in st.session_state:
    st.session_state.selected_patient = None
if 'patient_messages' not in st.session_state:
    st.session_state.patient_messages = {}

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

# Patient selection page
if st.session_state.selected_patient is None:
    st.markdown("# 🏥 Select Patient")
    st.markdown("---")
    
    # Load all patient JSON files
    patient_files = glob.glob("PT-*.json")
    patients = []
    
    for file in patient_files:
        try:
            with open(file, 'r') as f:
                data = json.load(f)
                patients.append(data['patient'])
        except:
            pass
    
    if not patients:
        st.error("No patient data found.")
        st.stop()
    
    # Display patients in columns (3 per row)
    cols_per_row = 3
    for i in range(0, len(patients), cols_per_row):
        cols = st.columns(cols_per_row)
        for j, col in enumerate(cols):
            if i + j < len(patients):
                patient = patients[i + j]
                with col:
                    st.markdown(f"""
                    <div style='
                        background: white;
                        padding: 1.5rem;
                        border-radius: 10px;
                        border-left: 4px solid #0066cc;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        margin-bottom: 1rem;
                        min-height: 220px;
                    '>
                        <h3 style='margin: 0 0 0.5rem 0; color: #0066cc;'>{patient['full_name']}</h3>
                        <p style='margin: 0.25rem 0; color: #666;'><strong>ID:</strong> {patient['id']}</p>
                        <p style='margin: 0.25rem 0; color: #666;'><strong>Age:</strong> {patient['age']}</p>
                        <p style='margin: 0.25rem 0; color: #666;'><strong>Room:</strong> {patient['room_number']}</p>
                        <p style='margin: 0.25rem 0; color: #666;'><strong>Diagnosis:</strong> {patient['primary_diagnosis']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"View Patient", key=f"btn_{patient['id']}", use_container_width=True):
                        st.session_state.selected_patient = patient
                        st.rerun()
    
    st.stop()  # Stop execution here if no patient selected

# Get selected patient data
selected_patient = st.session_state.selected_patient

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

# Add back button outside the loop
if st.button("← Back to Patients"):
    st.session_state.selected_patient = None
    st.rerun()

st.markdown("---")

# Placeholder for dynamic content that updates
placeholder = st.empty()

# Placeholder for the comment form (separate from the updating content)
comment_placeholder = st.empty()

# Add doctor comment form (outside loop to avoid duplicate widget error)
with comment_placeholder.container():
    st.markdown("### 💬 Send Update to Patient")
    with st.form("doctor_message_form", clear_on_submit=True):
        doctor_message = st.text_area("Doctor's message:", placeholder="Enter update for the patient...", height=100)
        submit_msg = st.form_submit_button("Send Update", use_container_width=True)
        
        if submit_msg and doctor_message.strip():
            patient_id = selected_patient['id']
            new_message = {
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'message': doctor_message.strip()
            }
            st.session_state.patient_messages[patient_id].append(new_message)
            
            # Publish message to MQTT broker
            try:
                publish_doctor_message(patient_id, doctor_message.strip())
            except Exception as e:
                st.error(f"Failed to publish to MQTT: {e}")
            
            st.rerun()

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
        "patient": {"name": selected_patient['full_name']},
        "summary": selected_patient.get('doctor_notes', 'No notes available'),
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
            st.write(f"**Room:** {selected_patient['room_number']}")
            st.write(f"**Diagnosis:** {selected_patient['primary_diagnosis']}")
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
            
            # Medications Section
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("#### 💊 Current Medications")
            medications = selected_patient.get('metrics', {}).get('medicine_taken', [])
            
            if not medications:
                st.write("No medications recorded.")
            else:
                for med in medications:
                    med_name = med.get('name', 'Unknown')
                    dosage = med.get('dosage', 'N/A')
                    status = med.get('status', 'N/A')
                    last_admin = med.get('last_administered', '')
                    
                    # Format last administered time
                    if last_admin:
                        try:
                            last_time = _local_t(last_admin)
                        except:
                            last_time = last_admin
                    else:
                        last_time = "N/A"
                    
                    st.markdown(f"""
                    <div style='background: #f8f9fa; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.75rem; border-left: 3px solid #28a745;'>
                        <strong style='color: #212529; font-size: 1.1rem;'>{med_name}</strong><br>
                        <span style='color: #6c757d;'>📋 <strong>Dosage:</strong> {dosage}</span><br>
                        <span style='color: #6c757d;'>⏱️ <strong>Schedule:</strong> {status}</span><br>
                        <span style='color: #6c757d;'>🕐 <strong>Last Given:</strong> {last_time}</span>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with c2:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.markdown("#### Care Team Updates")
            
            # Get patient-specific messages
            patient_id = selected_patient['id']
            if patient_id not in st.session_state.patient_messages:
                st.session_state.patient_messages[patient_id] = []
            
            feed = st.session_state.patient_messages[patient_id]
            
            if not feed:
                st.write("No updates yet.")
            else:
                for item in feed:
                    st.markdown(f"""
                    <div style='background: #f8f9fa; padding: 0.75rem; border-radius: 8px; margin-bottom: 0.5rem; border: 1px solid #dee2e6;'>
                        <strong style='color: #0066cc;'>{item['time']}</strong> <span style='color: #212529;'>— {item['message']}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("<hr style='margin: 1rem 0;'>", unsafe_allow_html=True)
            st.caption("These updates are informational only. For urgent questions, contact the care team directly.")
            st.markdown("</div>", unsafe_allow_html=True)
    
    # Wait 5 second before next update
    time.sleep(5)