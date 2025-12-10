def check_clinical_rules(vitals):
    """
    Deterministic clinical rules for immediate alerts.
    vitals: dict containing hr, sbp, spo2, temp, rr
    """
    alerts = []
    
    hr = vitals.get('hr', 80)
    sbp = vitals.get('sbp', 120)
    spo2 = vitals.get('spo2', 98)
    temp = vitals.get('temp', 37.0)
    rr = vitals.get('rr', 16)
    
    # Rule 1: Severe Hypotension
    if sbp < 90 and hr > 100:
        alerts.append({
            "code": "HYPOTENSION_SHOCK",
            "severity": "Critical",
            "rationale": f"Hypotension (SBP {sbp}) with Tachycardia (HR {hr}) suggests shock."
        })
        
    # Rule 2: Hypoxemia
    if spo2 < 90:
        alerts.append({
            "code": "HYPOXEMIA",
            "severity": "Critical",
            "rationale": f"SpO2 {spo2}% indicates respiratory failure."
        })
    elif spo2 < 94:
        alerts.append({
            "code": "DESATURATION",
            "severity": "High",
            "rationale": f"SpO2 {spo2}% requires monitoring."
        })
        
    # Rule 3: Sepsis Warning (qSOFA-like)
    qsofa = 0
    if rr >= 22: qsofa += 1
    if sbp <= 100: qsofa += 1
    # GCS not available, sub with confusion check in symptoms usually, but here vitals only
    
    # SIRS-like
    sirs = 0
    if temp > 38.0 or temp < 36.0: sirs += 1
    if hr > 90: sirs += 1
    if rr > 20: sirs += 1
    
    if sirs >= 2:
        alerts.append({
            "code": "SEPSIS_SIRS",
            "severity": "High",
            "rationale": f"SIRS criteria met (Temp {temp}, HR {hr}, RR {rr}). Monitor for sepsis."
        })
        
    # Rule 4: Severe Tachycardia/Bradycardia
    if hr > 130:
        alerts.append({
            "code": "TACHYCARDIA_SEVERE",
            "severity": "High",
            "rationale": f"HR {hr} bpm."
        })
    elif hr < 40:
        alerts.append({
            "code": "BRADYCARDIA_SEVERE",
            "severity": "High",
            "rationale": f"HR {hr} bpm."
        })
        
    return alerts
