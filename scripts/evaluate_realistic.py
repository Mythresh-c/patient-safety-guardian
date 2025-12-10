import os
import subprocess
import pandas as pd
import json

def run_evaluation():
    print("1. Generating Realistic Data...")
    subprocess.run(["python", "data_generator.py", "--n", "1000", "--realistic"])
    
    print("2. Training Model...")
    subprocess.run(["python", "train_model.py"])
    
    print("3. Running Pipeline on Test Samples...")
    subprocess.run(["python", "pipeline.py"])
    
    print("4. Verifying Outputs...")
    if os.path.exists("evidence/feature_importances.json"):
        print("Feature importances generated.")
    if os.path.exists("models/risk_model.pkl"):
        print("Model saved.")
        
    print("Evaluation Complete. Ready for UI.")

if __name__ == "__main__":
    run_evaluation()
