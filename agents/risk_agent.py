import pandas as pd
import joblib
import os
import json

class RiskAgent:
    def __init__(self, model_path='models/risk_model.pkl'):
        self.model_path = model_path
        self.pipeline = None
        self.feature_importances = {}
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.pipeline = joblib.load(self.model_path)
                # Load feature importances if available
                if os.path.exists('evidence/feature_importances.json'):
                    with open('evidence/feature_importances.json', 'r') as f:
                        self.feature_importances = json.load(f)
            except Exception as e:
                print(f"Error loading model: {e}")
        else:
            print(f"Model file not found at {self.model_path}")

    def predict(self, sample_dict):
        if not self.pipeline:
            return {"risk_score": 0.0, "risk_level": "Unknown", "top_features": []}

        try:
            input_data = pd.DataFrame([sample_dict])
            
            # Ensure columns
            required_cols = ['hr', 'sbp', 'dbp', 'spo2', 'temp', 'rr', 'age', 'sex', 'chronic_conditions']
            for col in required_cols:
                if col not in input_data.columns:
                    input_data[col] = 0 if col != 'chronic_conditions' and col != 'sex' else 'None'
            
            # Predict Proba (Calibrated if pipeline is calibrated)
            prediction = self.pipeline.predict_proba(input_data)[:, 1][0]
            
            # Uncertainty (Mock if not ensemble)
            uncertainty = 0.05 # Placeholder
            
            risk_level = "Low"
            if prediction > 0.7:
                risk_level = "High"
            elif prediction > 0.4:
                risk_level = "Medium"

            # Top Features (Global importance fallback if local not available)
            # In a real scenario, use SHAP here. For now, return top global features.
            top_features = sorted(self.feature_importances.items(), key=lambda x: x[1], reverse=True)[:3]
            top_features_list = [f"{k} ({v:.2f})" for k, v in top_features]

            return {
                "risk_score": float(prediction),
                "risk_level": risk_level,
                "uncertainty": uncertainty,
                "top_features": top_features_list,
                "calibrated_score": float(prediction)
            }
            
        except Exception as e:
            print(f"Prediction error: {e}")
            return {"risk_score": 0.0, "risk_level": "Error", "top_features": []}
