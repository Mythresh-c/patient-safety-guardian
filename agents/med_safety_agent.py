import pandas as pd
import Levenshtein
import datetime
import os

class MedicationSafetyAgent:
    def __init__(self, rules_path='data/med_rules.csv'):
        try:
            self.rules = pd.read_csv(rules_path)
        except FileNotFoundError:
            self.rules = pd.DataFrame()
            print("Warning: Med rules file not found.")

    def check(self, med_input):
        # 1. Input Parsing
        if isinstance(med_input, str):
            med_list = [m.strip() for m in med_input.split(',') if m.strip()]
        elif isinstance(med_input, list):
            med_list = [str(m).strip() for m in med_input if str(m).strip()]
        else:
            med_list = []

        interactions = []
        severity_score = 0.0
        
        if not med_list or len(med_list) < 2:
            return {"interactions": [], "severity_score": 0.0}

        # 2. Canonicalization
        # Load rules drugs for matching
        if not self.rules.empty:
            known_drugs = set(self.rules['drug_a'].unique()) | set(self.rules['drug_b'].unique())
        else:
            known_drugs = set()
        
        canonical_meds = []
        for med in med_list:
            best_match = None
            best_ratio = 0.0
            
            # Exact match first (case insensitive)
            for known in known_drugs:
                if med.lower() == known.lower():
                    best_match = known
                    best_ratio = 1.0
                    break
            
            # Fuzzy match
            if not best_match:
                for known in known_drugs:
                    ratio = Levenshtein.ratio(med.lower(), known.lower())
                    if ratio > 0.7:
                        if ratio > best_ratio:
                            best_ratio = ratio
                            best_match = known
            
            if best_match:
                canonical_meds.append(best_match)
            else:
                canonical_meds.append(med)

        # 3. Interaction Checking
        if not self.rules.empty:
            for i in range(len(canonical_meds)):
                for j in range(i + 1, len(canonical_meds)):
                    drug1 = canonical_meds[i]
                    drug2 = canonical_meds[j]
                    
                    # Check both directions
                    match = self.rules[
                        ((self.rules['drug_a'].str.lower() == drug1.lower()) & (self.rules['drug_b'].str.lower() == drug2.lower())) |
                        ((self.rules['drug_a'].str.lower() == drug2.lower()) & (self.rules['drug_b'].str.lower() == drug1.lower()))
                    ]
                    
                    if not match.empty:
                        row = match.iloc[0]
                        severity = row['severity']
                        
                        score_map = {'Low': 0.2, 'Medium': 0.5, 'High': 0.8, 'Critical': 1.0}
                        severity_score += score_map.get(severity, 0.0)
                        
                        interaction = {
                            "pair": [drug1, drug2],
                            "severity": severity,
                            "mechanism": row.get('mechanism', 'Unknown'),
                            "explanation": row['explanation'],
                            "recommended_action": row['recommended_action'],
                            "source": row.get('source', 'Unknown')
                        }
                        interactions.append(interaction)

        # Cap score
        severity_score = min(severity_score, 1.0)
        
        return {
            "interactions": interactions,
            "severity_score": severity_score
        }
