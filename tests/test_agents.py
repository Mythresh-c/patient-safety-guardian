import pytest
import os
import json
from agents.symptom_agent import SymptomAgent
from agents.med_safety_agent import MedicationSafetyAgent
from agents.priority_agent import PriorityAgent

def test_symptom_agent():
    agent = SymptomAgent()
    text = "Patient has chest pain and fever. Taking Aspirin."
    res = agent.extract(text)
    assert "chest pain" in res['symptoms']
    assert "fever" in res['symptoms']
    # Note: Aspirin might be in meds_list depending on agent logic (regex vs spacy)
    # Our regex logic checks lower case
    assert "aspirin" in [m.lower() for m in res['medications_mentioned']]

def test_med_safety_agent():
    # Ensure rules exist or mock them. 
    # We assume data/med_rules.csv exists from generator.
    if not os.path.exists('data/med_rules.csv'):
        pytest.skip("Med rules not found")
        
    agent = MedicationSafetyAgent()
    # Warfarin + Aspirin is a known high interaction in our generator
    res = agent.check(['Warfarin', 'Aspirin'])
    assert len(res['interactions']) > 0
    assert res['interactions'][0]['severity'] == 'High'

def test_priority_agent():
    agent = PriorityAgent()
    # High risk case
    res = agent.decide(
        {"symptoms": ["chest pain"]}, 
        {"severity_score": 0.8}, 
        {"risk_score": 0.9}
    )
    assert res['priority'] in ['High', 'Critical']
    
    # Low risk case
    res = agent.decide(
        {"symptoms": []}, 
        {"severity_score": 0.0}, 
        {"risk_score": 0.1}
    )
    assert res['priority'] == 'Low'
