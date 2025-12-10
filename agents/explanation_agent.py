import datetime

class ExplanationAgent:
    def __init__(self):
        self.template = """
Patient Safety Guardian Report
------------------------------
Patient ID: {patient_id}
Timestamp: {timestamp}

Summary:
The patient presents with {symptoms}. 
Risk Assessment: {risk_level} risk of deterioration (Score: {risk_score:.2f}).
Priority Level: {priority}

Medication Safety:
{med_safety_summary}

Clinical Recommendation:
{recommendation}
"""

    def generate(self, patient_id, timestamp, symptom_json, med_json, risk_json, priority_json, routing_json=None):
        symptoms = ", ".join(symptom_json.get('symptoms', [])) or "no specific symptoms"
        
        med_interactions = med_json.get('interactions', [])
        if med_interactions:
            med_safety_summary = f"Detected {len(med_interactions)} interaction(s). "
            for i in med_interactions:
                med_safety_summary += f"\n- {i['pair'][0]} + {i['pair'][1]}: {i['severity']} severity. {i['explanation']}"
        else:
            med_safety_summary = "No significant medication interactions detected."
            
        priority = priority_json.get('priority', 'Low')
        
        rec = "Continue routine monitoring."
        if priority == "Critical":
            rec = "IMMEDIATE CLINICAL REVIEW REQUIRED. Assess vitals and review medication list."
        elif priority == "High":
            rec = "Urgent review recommended. Monitor for deterioration."
        elif priority == "Medium":
            rec = "Review within 4 hours. Check medication interactions."
            
        routing_info = ""
        if routing_json and routing_json.get('escalated'):
            routing_info = f"\nAssigned to {routing_json['assigned_to']} ({routing_json['team']}) — Action: {routing_json['action']}"

        return self.template.format(
            patient_id=patient_id,
            timestamp=timestamp,
            symptoms=symptoms,
            risk_level=risk_json.get('risk_level', 'Unknown'),
            risk_score=risk_json.get('risk_score', 0.0),
            priority=priority,
            med_safety_summary=med_safety_summary,
            recommendation=rec
        ) + routing_info
