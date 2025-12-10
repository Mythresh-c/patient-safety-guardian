import streamlit as st
import pandas as pd
import json
import datetime
import os
import csv
from agents.symptom_agent import SymptomAgent
from agents.med_safety_agent import MedicationSafetyAgent
from agents.risk_agent import RiskAgent
from agents.priority_agent import PriorityAgent
from agents.explanation_agent import ExplanationAgent
from agents.routing_agent import RoutingAgent
from rules.clinical_alerts import check_clinical_rules
from utils import ensure_dirs

st.set_page_config(page_title="Patient Safety Guardian", layout="wide")

# Inject Custom CSS
st.markdown("""
<style>
.clinical-card {
    background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
    color: #212529 !important;
    padding: 25px;
    border-radius: 12px;
    border-left: 6px solid #007bff;
    box-shadow: 0 4px 12px rgba(0,0,0,0.08); /* Improved shadow */
    margin-bottom: 20px;
}
.clinical-card.high-risk { border-left-color: #dc3545; background: linear-gradient(135deg, #fff5f5 0%, #ffe3e3 100%); }
.clinical-card.medium-risk { border-left-color: #ffc107; background: linear-gradient(135deg, #fff9db 0%, #fff3cd 100%); }
.clinical-card * { color: #212529 !important; }
.alert-box {
    padding: 15px;
    background-color: #f8d7da;
    color: #721c24;
    border: 1px solid #f5c6cb;
    border-radius: 5px;
    margin-bottom: 15px;
}
.sidebar-table {
    width: 100%;
    font-size: 14px;
}
.sidebar-table td {
    padding: 5px;
    vertical-align: top;
}
.sidebar-table .label {
    font-weight: bold;
    color: #88ccee;
    width: 40%;
}
/* Table Borders in Agent Breakdown */
[data-testid="stDataFrame"] {
    border: 1px solid #e0e0e0;
    border-radius: 5px;
    padding: 5px;
}
</style>
""", unsafe_allow_html=True)

def log_action(patient_id, action, user="Clinician", reason=None):
    ensure_dirs(['evidence'])
    file_path = 'evidence/actions_log.csv'
    if not os.path.exists(file_path):
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'patient_id', 'action', 'user', 'reason'])
    with open(file_path, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([datetime.datetime.now().isoformat(), patient_id, action, user, reason])

def run_analysis(sample):
    symptom_agent = SymptomAgent()
    med_agent = MedicationSafetyAgent()
    risk_agent = RiskAgent()
    priority_agent = PriorityAgent()
    routing_agent = RoutingAgent()
    explanation_agent = ExplanationAgent()

    symptom_out = symptom_agent.extract(sample.get('clinical_note', ''))
    
    meds_input = sample.get('medications', '')
    if not meds_input:
        meds_input = symptom_out['medications_mentioned']
    
    # Ensure list for agent
    if isinstance(meds_input, str):
        meds_list = [m.strip() for m in meds_input.split(',') if m.strip()]
    elif isinstance(meds_input, list):
        meds_list = [str(m).strip() for m in meds_input if str(m).strip()]
    else:
        meds_list = []

    med_out = med_agent.check(meds_list)
    risk_out = risk_agent.predict(sample)
    
    # Clinical Alerts
    vitals = {k: sample.get(k) for k in ['hr', 'sbp', 'spo2', 'temp', 'rr']}
    alerts = check_clinical_rules(vitals)
    
    priority_out = priority_agent.decide(symptom_out, med_out, risk_out)
    
    # Escalate priority if alerts exist
    if alerts and priority_out['priority'] not in ['High', 'Critical']:
        priority_out['priority'] = 'High'
        priority_out['reasons'].append("Clinical Rule Alert Triggered")
        
    routing_out = routing_agent.route(priority_out, sample.get('patient_id'), alerts)
    
    explanation = explanation_agent.generate(
        sample.get('patient_id', 'Unknown'), 
        sample.get('timestamp', datetime.datetime.now().isoformat()),
        symptom_out, med_out, risk_out, priority_out, routing_out
    )
    
    return {
        "symptom_out": symptom_out,
        "med_out": med_out,
        "risk_out": risk_out,
        "priority_out": priority_out,
        "routing_out": routing_out,
        "explanation": explanation,
        "alerts": alerts
    }

st.title("🏥 Patient Safety Guardian")

# Layout: Sidebar (Narrow) + Main (Wide)
with st.sidebar:
    st.header("Input Data")
    input_mode = st.radio("Choose Input Mode", ["Load Sample", "Custom Entry"])

    sample_data = {}
    timeseries_df = pd.DataFrame()

    if input_mode == "Load Sample":
        try:
            with open('data/test_samples.json', 'r') as f:
                samples = json.load(f)
            sample_ids = [s['patient_id'] for s in samples]
            selected_id = st.selectbox("Select Patient", sample_ids)
            sample_data = next(s for s in samples if s['patient_id'] == selected_id)
            
            # Load Time Series
            if os.path.exists('data/patient_data_timeseries.csv'):
                ts_all = pd.read_csv('data/patient_data_timeseries.csv')
                timeseries_df = ts_all[ts_all['patient_id'] == selected_id]
                
        except FileNotFoundError:
            st.error("Data not found. Run data_generator.py first.")
    else:
        # Custom Entry (Simplified)
        pid = st.text_input("Patient ID", "P99999")
        note = st.text_area("Clinical Note", "Patient complains of chest pain.")
        meds = st.text_input("Medications", "Aspirin, Warfarin")
        sample_data = {
            "patient_id": pid, "clinical_note": note, "medications": meds,
            "hr": st.number_input("HR", 80), "sbp": st.number_input("SBP", 120),
            "spo2": st.number_input("SpO2", 98), "temp": st.number_input("Temp", 37.0),
            "rr": st.number_input("RR", 16), "age": 65, "sex": "M", "chronic_conditions": "None"
        }

    # Sidebar Table
    if sample_data:
        st.markdown("### Patient Details")
        table_html = "<table class='sidebar-table'>"
        for key, value in sample_data.items():
            if key in ['patient_id', 'age', 'sex', 'chronic_conditions', 'clinical_note', 'medications']:
                label = key.replace('_', ' ').title()
                val_str = str(value)
                table_html += f"<tr><td class='label'>{label}</td><td>{val_str}</td></tr>"
        table_html += "</table>"
        st.markdown(table_html, unsafe_allow_html=True)
        
    run_btn = st.button("Run Analysis", type="primary")

# Main Content
if run_btn:
    with st.spinner("Analyzing..."):
        results = run_analysis(sample_data)
        
        # Alerts Banner
        if results['alerts']:
            for alert in results['alerts']:
                st.markdown(f"<div class='alert-box'><strong>{alert['code']}</strong>: {alert['rationale']}</div>", unsafe_allow_html=True)

        # KPIs with Icons
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("⚠️ Risk Level", results['risk_out']['risk_level'], f"Score: {results['risk_out']['risk_score']:.2f}")
        c2.metric("🚑 Priority", results['priority_out']['priority'])
        c3.metric("💊 Interactions", len(results['med_out']['interactions']))
        c4.metric("🩺 Symptoms", len(results['symptom_out']['symptoms']))
        
        # Vitals Trend
        if not timeseries_df.empty:
            st.divider()
            st.subheader("Vitals Trend (Last 12h)")
            
            df_vitals = timeseries_df.copy()
            df_vitals['timestamp'] = pd.to_datetime(df_vitals['timestamp'])
            df_vitals = df_vitals.sort_values('timestamp')
            
            # Relative Time Labels
            last_time = df_vitals['timestamp'].max()
            # Create readable labels like "-4h"
            df_vitals['Time Label'] = df_vitals['timestamp'].apply(lambda x: f"{int((x - last_time).total_seconds() / 3600)}h" if (x - last_time).total_seconds() != 0 else "Now")
            
            # Downsample if too many points (take last 8)
            if len(df_vitals) > 8:
                df_vitals = df_vitals.tail(8)
            
            c1, c2, c3 = st.columns(3)
            
            with c1:
                st.caption("Heart Rate (bpm)")
                st.line_chart(df_vitals.set_index('Time Label')['hr'], height=120)
                curr = df_vitals['hr'].iloc[-1]
                st.markdown(f"**Min:** {df_vitals['hr'].min()} | **Max:** {df_vitals['hr'].max()} | **Last:** {curr}")
                
            with c2:
                st.caption("Systolic BP (mmHg)")
                st.line_chart(df_vitals.set_index('Time Label')['sbp'], height=120)
                curr = df_vitals['sbp'].iloc[-1]
                st.markdown(f"**Min:** {df_vitals['sbp'].min()} | **Max:** {df_vitals['sbp'].max()} | **Last:** {curr}")
                
            with c3:
                st.caption("SpO2 (%)")
                st.line_chart(df_vitals.set_index('Time Label')['spo2'], height=120)
                curr = df_vitals['spo2'].iloc[-1]
                st.markdown(f"**Min:** {df_vitals['spo2'].min()} | **Max:** {df_vitals['spo2'].max()} | **Last:** {curr}")

        st.divider()
        
        # Routing Badge
        routing = results['routing_out']
        badge_color = "#dc3545" if routing['escalated'] else "#0d6efd"
        st.markdown(f"""
        <div style='margin-bottom:10px;'>
            <span style='background-color:{badge_color}; color:white; padding:8px 12px; border-radius:5px; font-weight:bold;'>
                Assigned to: {routing['assigned_to']} ({routing['team']})
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Explanation Card
        card_class = "clinical-card"
        if results['risk_out']['risk_level'] == "High": card_class += " high-risk"
        elif results['risk_out']['risk_level'] == "Medium": card_class += " medium-risk"
        
        st.markdown(f"""
        <div class="{card_class}">
            <h4 style='margin-top:0; border-bottom:1px solid #ddd; padding-bottom:10px;'>Clinical Summary</h4>
            {results['explanation'].replace(chr(10), '<br>')}
        </div>
        """, unsafe_allow_html=True)
        
        # Clinician Actions
        st.markdown("### Clinician Actions")
        c1, c2, c3 = st.columns(3)
        if c1.button("Acknowledge", use_container_width=True):
            log_action(sample_data['patient_id'], "Acknowledged")
            st.toast("Assignment logged ✓")
        if c2.button("Assign to Me", use_container_width=True):
            log_action(sample_data['patient_id'], "Assigned to Self")
            st.toast("Assignment logged ✓")
            
        with c3:
            with st.popover("Override Routing", use_container_width=True):
                reason = st.text_input("Reason for override")
                if st.button("Confirm Override"):
                    if reason:
                        log_action(sample_data['patient_id'], "Override Routing", reason=reason)
                        st.toast("Override logged ✓")
                    else:
                        st.error("Reason required")

        st.divider()

        # Tabs
        st.subheader("Agent Breakdown")
        t1, t2, t3, t4 = st.tabs(["Symptoms", "Med Safety", "Risk Model", "Priority"])
        
        with t1:
            st.dataframe(pd.DataFrame(results['symptom_out']['symptoms'], columns=["Symptom"]), use_container_width=True, hide_index=True)
            
        with t2:
            interactions = results['med_out']['interactions']
            if interactions:
                # Flatten for display
                flat_ints = []
                for i in interactions:
                    flat_ints.append({
                        "Drug A": i['pair'][0],
                        "Drug B": i['pair'][1],
                        "Severity": i['severity'],
                        "Mechanism": i.get('mechanism', 'Unknown'),
                        "Recommended Action": i.get('recommended_action', 'N/A'),
                        "Source": i.get('source', 'Unknown')
                    })
                st.dataframe(pd.DataFrame(flat_ints), use_container_width=True, hide_index=True)
            else:
                st.info("No clinically significant interactions identified.")
                
        with t3:
            c1, c2 = st.columns([1, 2])
            with c1:
                st.metric("Risk Score", f"{results['risk_out']['risk_score']:.4f}")
                st.metric("Risk Level", results['risk_out']['risk_level'])
            with c2:
                st.write("Top Features:")
                st.dataframe(pd.DataFrame(results['risk_out']['top_features'], columns=["Feature"]), use_container_width=True, hide_index=True)
                
        with t4:
            p_out = results['priority_out']
            st.write(f"**Priority:** {p_out['priority']}")
            st.write("**Reasons:**")
            st.dataframe(pd.DataFrame(p_out.get('reasons', []), columns=["Reason"]), use_container_width=True, hide_index=True)
