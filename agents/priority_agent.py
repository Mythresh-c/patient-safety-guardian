class PriorityAgent:
    def __init__(self):
        self.weights = {
            'risk': 0.6,
            'med_severity': 0.25,
            'symptom_severity': 0.15
        }

    def decide(self, symptom_json, med_json, risk_json):
        risk_score = risk_json.get('risk_score', 0.0)
        med_score = med_json.get('severity_score', 0.0)
        
        # Simple symptom severity heuristic
        symptoms = symptom_json.get('symptoms', [])
        critical_symptoms = ['chest pain', 'shortness of breath', 'confusion']
        symptom_score = 0.0
        for s in symptoms:
            if s.lower() in critical_symptoms:
                symptom_score = 1.0
                break
        if not symptom_score and symptoms:
            symptom_score = 0.3 # Base score for any symptom
            
        final_score = (
            risk_score * self.weights['risk'] +
            med_score * self.weights['med_severity'] +
            symptom_score * self.weights['symptom_severity']
        )
        
        priority = "Low"
        if final_score > 0.8:
            priority = "Critical"
        elif final_score > 0.6:
            priority = "High"
        elif final_score > 0.4:
            priority = "Medium"
            
        reasons = []
        if risk_score > 0.7:
            reasons.append("High deterioration risk detected.")
        if med_score > 0.5:
            reasons.append("Significant medication interactions found.")
        if symptom_score > 0.8:
            reasons.append("Critical symptoms reported.")
            
        return {
            "priority": priority,
            "score": round(final_score, 2),
            "reasons": reasons
        }
