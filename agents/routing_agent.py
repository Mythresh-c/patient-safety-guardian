import random
import csv
import datetime
import os
from utils import ensure_dirs

class RoutingAgent:
    def __init__(self):
        self.rota = {
            "Cardiology": ["Dr. Smith", "Dr. Heart"],
            "Respiratory": ["Dr. Lung", "Dr. Breath"],
            "Internal Medicine": ["Dr. Jones", "Dr. House"],
            "Critical Care": ["Dr. Patel", "Dr. Critical"],
            "General": ["Dr. Doe", "Dr. Ray"]
        }
        self.audit_file = 'evidence/routing_log.csv'
        ensure_dirs(['evidence'])
        if not os.path.exists(self.audit_file):
            with open(self.audit_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'patient_id', 'priority', 'reason', 'assigned_to', 'team', 'escalated_by'])

    def route(self, priority_out, patient_id, alerts=None):
        priority = priority_out.get('priority', 'Low')
        reasons = priority_out.get('reasons', [])
        
        assigned_to = "Routine Queue"
        team = "General Ward"
        action = "Routine Monitoring"
        escalated = False
        
        # Determine Specialist based on reasons/alerts
        specialty = "Internal Medicine"
        
        combined_reasons = " ".join(reasons).lower()
        if alerts:
            for alert in alerts:
                combined_reasons += " " + alert['rationale'].lower()
        
        if "chest pain" in combined_reasons or "heart" in combined_reasons or "hypotension" in combined_reasons:
            specialty = "Cardiology"
        elif "breath" in combined_reasons or "spo2" in combined_reasons or "hypoxemia" in combined_reasons:
            specialty = "Respiratory"
        elif "sepsis" in combined_reasons or "shock" in combined_reasons:
            specialty = "Critical Care"
            
        if priority in ['High', 'Critical'] or (alerts and len(alerts) > 0):
            escalated = True
            team = specialty
            assigned_to = random.choice(self.rota.get(team, self.rota["General"]))
            action = "Immediate Review"
            
        # Audit Log
        with open(self.audit_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.datetime.now().isoformat(),
                patient_id,
                priority,
                "; ".join(reasons),
                assigned_to,
                team,
                "System"
            ])
            
        return {
            "assigned_to": assigned_to,
            "team": team,
            "escalated": escalated,
            "action": action,
            "reason": f"Priority: {priority}. {specialty} indicated."
        }
