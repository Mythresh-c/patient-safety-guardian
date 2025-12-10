import argparse
import json
import pandas as pd
import datetime
from agents.symptom_agent import SymptomAgent
from agents.med_safety_agent import MedicationSafetyAgent
from agents.risk_agent import RiskAgent
from agents.priority_agent import PriorityAgent
from agents.explanation_agent import ExplanationAgent
from agents.routing_agent import RoutingAgent
from rules.clinical_alerts import check_clinical_rules
from utils import ensure_dirs, save_json, load_json

def run_pipeline(samples_path, out_dir):
    ensure_dirs([out_dir])
    
    # Load Agents
    symptom_agent = SymptomAgent()
    med_agent = MedicationSafetyAgent()
    risk_agent = RiskAgent()
    priority_agent = PriorityAgent()
    routing_agent = RoutingAgent()
    explanation_agent = ExplanationAgent()
    
    # Load Samples
    try:
        samples = load_json(samples_path)
    except FileNotFoundError:
        print(f"Samples file {samples_path} not found.")
        return

    results = []
    
    print(f"Running pipeline on {len(samples)} samples...")
    
    for sample in samples:
        pid = sample.get('patient_id', 'Unknown')
        print(f"Processing {pid}...")
        
        # 1. Symptom Extraction
        symptom_out = symptom_agent.extract(sample.get('clinical_note', ''))
        
        # 2. Med Safety
        # Ensure list of strings
        meds_input = sample.get('medications', '')
        if not meds_input:
            meds_input = symptom_out['medications_mentioned']
        
        # If string, split it. If list, keep it.
        if isinstance(meds_input, str):
            meds_list = [m.strip() for m in meds_input.split(',') if m.strip()]
        elif isinstance(meds_input, list):
            meds_list = [str(m).strip() for m in meds_input if str(m).strip()]
        else:
            meds_list = []
            
        med_out = med_agent.check(meds_list)
        
        # 3. Risk Prediction
        risk_out = risk_agent.predict(sample)
        
        # 4. Clinical Alerts
        vitals = {k: sample.get(k) for k in ['hr', 'sbp', 'spo2', 'temp', 'rr']}
        alerts = check_clinical_rules(vitals)
        
        # 5. Priority
        priority_out = priority_agent.decide(symptom_out, med_out, risk_out)
        
        # Escalate if alerts
        if alerts and priority_out['priority'] not in ['High', 'Critical']:
            priority_out['priority'] = 'High'
            priority_out['reasons'].append("Clinical Rule Alert Triggered")
        
        # 6. Routing
        routing_out = routing_agent.route(priority_out, pid, alerts)
        
        # 7. Explanation
        explanation = explanation_agent.generate(
            pid, 
            sample.get('timestamp', datetime.datetime.now().isoformat()),
            symptom_out, med_out, risk_out, priority_out, routing_out
        )
        
        result = {
            "patient_id": pid,
            "symptoms": symptom_out['symptoms'],
            "medications_mentioned": meds_list,
            "interactions": med_out['interactions'],
            "risk_score": risk_out['risk_score'],
            "risk_level": risk_out['risk_level'],
            "priority": priority_out['priority'],
            "routing": routing_out,
            "explanation": explanation,
            "alerts": alerts
        }
        results.append(result)
        
    # Save Consolidated Results
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_json = f"{out_dir}/results_{timestamp}.json"
    save_json(results, out_json)
    print(f"Results saved to {out_json}")
    
    # Generate Markdown Report
    report_path = f"{out_dir}/report_{timestamp}.md"
    with open(report_path, 'w') as f:
        f.write(f"# Patient Safety Guardian Report - {timestamp}\n\n")
        for res in results:
            f.write(f"## Patient {res['patient_id']}\n")
            f.write(f"**Priority:** {res['priority']}\n")
            f.write(f"**Risk Level:** {res['risk_level']} (Score: {res['risk_score']:.2f})\n")
            f.write(f"**Assigned To:** {res['routing']['assigned_to']} ({res['routing']['team']})\n")
            if res['alerts']:
                f.write("**ALERTS:**\n")
                for a in res['alerts']:
                    f.write(f"- {a['code']}: {a['rationale']}\n")
            f.write(f"**Symptoms:** {', '.join(res['symptoms'])}\n")
            f.write(f"**Interactions:** {len(res['interactions'])}\n")
            f.write("### Clinical Explanation\n")
            f.write(f"{res['explanation']}\n")
            f.write("---\n")
    print(f"Report saved to {report_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--samples', type=str, default='data/test_samples.json')
    parser.add_argument('--out_dir', type=str, default='evidence')
    args = parser.parse_args()
    run_pipeline(args.samples, args.out_dir)
