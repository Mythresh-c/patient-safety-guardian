import argparse
import pandas as pd
import numpy as np
import random
import json
from utils import seed_everything, ensure_dirs

def generate_data(n_samples, seed, realistic=True):
    seed_everything(seed)
    ensure_dirs(['data'])

    # Constants
    MEDICATIONS = [
        'Aspirin', 'Ibuprofen', 'Paracetamol', 'Amoxicillin', 'Metformin', 
        'Lisinopril', 'Atorvastatin', 'Warfarin', 'Clopidogrel', 'Simvastatin', 
        'Levothyroxine', 'Omeprazole', 'Amlodipine', 'Metoprolol', 'Albuterol', 
        'Gabapentin', 'Hydrochlorothiazide', 'Losartan', 'Furosemide', 'Pantoprazole',
        'Spironolactone', 'Insulin', 'Sildenafil', 'Nitroglycerin', 'Methotrexate',
        'Penicillin', 'Digoxin', 'Amiodarone', 'Calcium Carbonate', 'Ciprofloxacin',
        'Theophylline', 'Fluoxetine', 'Phenelzine', 'Tramadol', 'Propranolol',
        'Lithium', 'Carbamazepine', 'Erythromycin', 'Allopurinol', 'Azathioprine',
        'Contrast Dye', 'Doxycycline', 'Potassium Chloride', 'Gentamicin', 
        'Vancomycin', 'Piperacillin-Tazobactam', 'Citalopram', 'Ondansetron',
        'Phenytoin', 'Valproic Acid', 'Clozapine', 'Trimethoprim-Sulfamethoxazole',
        'Colchicine', 'Fluconazole', 'Rivaroxaban', 'Ketoconazole', 'Dabigatran',
        'Verapamil', 'Fentanyl', 'Midazolam', 'Ritonavir', 'Domperidone', 
        'Haloperidol', 'Levodopa', 'Prednisolone', 'Bisoprolol', 'Eplerenone', 'Trimethoprim'
    ]
    
    CONDITIONS = ['Hypertension', 'Diabetes', 'Asthma', 'COPD', 'Heart Disease', 'CKD', 'None', 'Arthritis', 'Anxiety', 'Depression']
    SYMPTOMS = ['Chest pain', 'Shortness of breath', 'Fever', 'Headache', 'Dizziness', 'Nausea', 'Fatigue', 'Palpitations', 'Cough', 'Sore throat', 'Abdominal pain', 'Back pain', 'Rash', 'Swelling', 'Confusion']

    summary_data = []
    timeseries_data = []

    for i in range(n_samples):
        pid = f'P{i:05d}'
        age = random.randint(18, 95)
        sex = random.choice(['M', 'F'])
        
        # Comorbidities
        num_conditions = np.random.poisson(1.5)
        patient_conditions = random.sample(CONDITIONS, min(len(CONDITIONS), max(1, num_conditions)))
        if 'None' in patient_conditions and len(patient_conditions) > 1:
            patient_conditions.remove('None')
        
        # Meds
        num_meds = np.random.poisson(3)
        patient_meds = random.sample(MEDICATIONS, min(len(MEDICATIONS), num_meds))
        
        # Force Interactions in ~30% of patients
        if random.random() < 0.3:
            pair = random.choice([
                ['Aspirin', 'Warfarin'],
                ['Lisinopril', 'Spironolactone'],
                ['Atorvastatin', 'Clarithromycin'],
                ['Sildenafil', 'Nitroglycerin'],
                ['Fluoxetine', 'Phenelzine'],
                ['Digoxin', 'Amiodarone'],
                ['Simvastatin', 'Amlodipine'],
                ['Citalopram', 'Ondansetron']
            ])
            for p in pair:
                if p not in patient_meds:
                    patient_meds.append(p)

        # Symptoms
        num_symptoms = np.random.poisson(1)
        patient_symptoms = random.sample(SYMPTOMS, min(len(SYMPTOMS), max(1, num_symptoms)))

        # Determine if deterioration event (15% chance)
        is_deteriorating = random.random() < 0.15
        deterioration_type = None
        if is_deteriorating:
            deterioration_type = random.choice(['sepsis', 'hypotension', 'hypoxemia'])

        # Generate Time Series (6-12 steps)
        num_steps = random.randint(6, 12)
        base_time = pd.Timestamp.now() - pd.Timedelta(hours=num_steps)
        
        # Baselines
        base_hr = random.randint(60, 90)
        base_sbp = random.randint(110, 140)
        base_dbp = random.randint(70, 90)
        base_spo2 = random.randint(95, 100)
        base_temp = random.uniform(36.5, 37.2)
        base_rr = random.randint(12, 18)
        
        if 'Hypertension' in patient_conditions:
            base_sbp += 15
            base_dbp += 10
        if 'COPD' in patient_conditions:
            base_spo2 -= 3
            base_rr += 2

        patient_ts = []
        
        current_hr = base_hr
        current_sbp = base_sbp
        current_dbp = base_dbp
        current_spo2 = base_spo2
        current_temp = base_temp
        current_rr = base_rr

        for t in range(num_steps):
            timestamp = base_time + pd.Timedelta(hours=t)
            
            # Random Walk
            current_hr += random.randint(-2, 2)
            current_sbp += random.randint(-3, 3)
            current_dbp += random.randint(-2, 2)
            current_spo2 += random.randint(-1, 1)
            current_temp += random.uniform(-0.1, 0.1)
            current_rr += random.randint(-1, 1)
            
            # Apply Deterioration Trend in last few steps
            if is_deteriorating and t > num_steps // 2:
                if deterioration_type == 'sepsis':
                    current_hr += random.randint(2, 5)
                    current_temp += random.uniform(0.1, 0.3)
                    current_sbp -= random.randint(1, 3)
                    current_rr += 1
                elif deterioration_type == 'hypotension':
                    current_sbp -= random.randint(3, 8)
                    current_dbp -= random.randint(2, 5)
                    current_hr += random.randint(1, 3) # Compensatory tachycardia
                elif deterioration_type == 'hypoxemia':
                    current_spo2 -= random.randint(1, 3)
                    current_rr += random.randint(1, 2)
                    current_hr += random.randint(1, 2)

            # Constraints
            current_spo2 = min(100, max(70, current_spo2))
            current_temp = round(current_temp, 1)
            
            patient_ts.append({
                'patient_id': pid,
                'timestamp': timestamp.isoformat(),
                'hr': int(current_hr),
                'sbp': int(current_sbp),
                'dbp': int(current_dbp),
                'spo2': int(current_spo2),
                'temp': current_temp,
                'rr': int(current_rr)
            })
            
        timeseries_data.extend(patient_ts)
        
        # Summary Data (Last reading + demographics)
        last_reading = patient_ts[-1]
        
        # Clinical Note Generation
        note = f"Patient {pid}, {age} year old {sex}. History of {', '.join(patient_conditions)}."
        note += f" Presents with {', '.join(patient_symptoms)}."
        if is_deteriorating:
            if deterioration_type == 'sepsis':
                note += " Fevers and chills reported. Possible infection source."
            elif deterioration_type == 'hypotension':
                note += " Feeling lightheaded and dizzy."
            elif deterioration_type == 'hypoxemia':
                note += " Increased work of breathing."
        
        summary_data.append({
            'patient_id': pid,
            'age': age,
            'sex': sex,
            'chronic_conditions': ", ".join(patient_conditions),
            'medications': ", ".join(patient_meds),
            'clinical_note': note,
            'symptoms': ", ".join(patient_symptoms),
            'hr': last_reading['hr'],
            'sbp': last_reading['sbp'],
            'dbp': last_reading['dbp'],
            'spo2': last_reading['spo2'],
            'temp': last_reading['temp'],
            'rr': last_reading['rr'],
            'deterioration_label': 1 if is_deteriorating else 0,
            'deterioration_type': deterioration_type if is_deteriorating else 'None',
            'timestamp': last_reading['timestamp']
        })

    # Save Files
    pd.DataFrame(summary_data).to_csv('data/patient_summary.csv', index=False)
    pd.DataFrame(timeseries_data).to_csv('data/patient_data_timeseries.csv', index=False)
    
    # Generate Test Samples JSON for Pipeline (subset)
    test_samples = []
    for i in range(min(10, n_samples)):
        row = summary_data[i].copy()
        test_samples.append(row)
    
    with open('data/test_samples.json', 'w') as f:
        json.dump(test_samples, f, indent=4)
        
    print(f"Generated data for {n_samples} patients.")
    print("Files: data/patient_summary.csv, data/patient_data_timeseries.csv, data/test_samples.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--n', type=int, default=1000)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--realistic', action='store_true')
    args = parser.parse_args()
    generate_data(args.n, args.seed, args.realistic)
