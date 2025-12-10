import re
try:
    import spacy
except ImportError:
    spacy = None

class SymptomAgent:
    def __init__(self):
        self.nlp = None
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except:
            print("Warning: spaCy model not found. Using regex fallback.")
        
        # Fallback lists
        self.SYMPTOMS_LIST = ['chest pain', 'shortness of breath', 'fever', 'headache', 'dizziness', 'nausea', 'fatigue', 'palpitations', 'cough', 'sore throat', 'abdominal pain', 'back pain', 'rash', 'swelling', 'confusion']
        self.MEDS_LIST = ['aspirin', 'ibuprofen', 'paracetamol', 'amoxicillin', 'metformin', 'lisinopril', 'atorvastatin', 'warfarin', 'clopidogrel', 'simvastatin', 'levothyroxine', 'omeprazole', 'amlodipine', 'metoprolol', 'albuterol', 'gabapentin', 'hydrochlorothiazide', 'losartan', 'furosemide', 'pantoprazole']

    def extract(self, note_text):
        if not note_text:
            return {"symptoms": [], "medications_mentioned": []}
            
        text_lower = note_text.lower()
        symptoms = []
        meds = []

        if self.nlp:
            doc = self.nlp(note_text)
            # Simple entity extraction if trained, but standard model might not catch all clinical terms.
            # Hybrid approach: use spaCy for noun chunks/entities and check against lists
            for ent in doc.ents:
                if ent.label_ == "PRODUCT" or ent.text.lower() in self.MEDS_LIST:
                    meds.append(ent.text)
            
            # Fallback to list check for robustness
            for s in self.SYMPTOMS_LIST:
                if s in text_lower:
                    symptoms.append(s)
            for m in self.MEDS_LIST:
                if m in text_lower and m not in [x.lower() for x in meds]:
                    meds.append(m)
        else:
            # Regex/String matching fallback
            for s in self.SYMPTOMS_LIST:
                if s in text_lower:
                    symptoms.append(s)
            for m in self.MEDS_LIST:
                if m in text_lower:
                    meds.append(m)
        
        return {
            "symptoms": list(set(symptoms)),
            "medications_mentioned": list(set(meds))
        }
