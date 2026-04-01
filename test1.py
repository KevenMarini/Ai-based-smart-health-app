import pandas as pd
import re
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.ensemble import RandomForestClassifier

# ==============================
# 1. LOAD DATASETS
# ==============================
# Ensure these paths match your local folder structure
try:
    df = pd.read_csv("archive (1)/dataset.csv")
    severity_df = pd.read_csv("archive (1)/Symptom-severity.csv")
    desc_df = pd.read_csv("archive (1)/symptom_Description.csv")
    precaution_df = pd.read_csv("archive (1)/symptom_precaution.csv")
except FileNotFoundError:
    # Fallback for standard filenames if 'archive (1)' folder isn't present
    df = pd.read_csv("dataset.csv")
    severity_df = pd.read_csv("Symptom-severity.csv")
    desc_df = pd.read_csv("symptom_Description.csv")
    precaution_df = pd.read_csv("symptom_precaution.csv")

# ==============================
# 2. PREPROCESS & TRAIN
# ==============================
symptom_columns = df.columns[1:]

def combine_symptoms(row):
    symptoms = []
    for col in symptom_columns:
        if pd.notna(row[col]):
            symptoms.append(str(row[col]).strip().lower())
    return symptoms

df['symptoms'] = df.apply(combine_symptoms, axis=1)

mlb = MultiLabelBinarizer()
X = mlb.fit_transform(df['symptoms'])
y = df['Disease']

model = RandomForestClassifier(n_estimators=300, random_state=42)
model.fit(X, y)

valid_symptoms = list(mlb.classes_)

# ==============================
# 3. 🔥 IMPROVED NLP EXTRACTION
# ==============================
def extract_symptoms(text):
    text = text.lower()
    found = []

    # Map common English words to clinical dataset terms
    synonym_map = {
        "cold": ["continuous_sneezing", "chills"],
        "fever": ["high_fever"],
        "throw up": ["vomiting"],
        "puke": ["vomiting"],
        "tired": ["fatigue"],
        "exhausted": ["fatigue"],
        "dizzy": ["dizziness"],
        "headache": ["headache"],
        "can't smell": ["loss_of_smell"],
        "stomach hurts": ["stomach_pain", "abdominal_pain"],
        "heartburn": ["acidity"],
        "itchy": ["itching"],
        "cough": ["cough"],
        "muscle pain": ["muscle_pain"],
        "shaking": ["shivering"]
    }

    # First: Check for synonyms using word boundaries
    for phrase, mapped_symptoms in synonym_map.items():
        if re.search(r'\b' + re.escape(phrase) + r'\b', text):
            found.extend(mapped_symptoms)

    # Second: Match exact dataset clinical phrases
    for symptom in valid_symptoms:
        clean_symptom = symptom.replace("_", " ")
        if clean_symptom in text:
            found.append(symptom)

    return list(set(found))

# ==============================
# 4. HELPER FUNCTIONS
# ==============================
def get_health_type(disease):
    d = disease.lower()
    if "fever" in d or "infection" in d: return "Infection"
    if "cold" in d or "cough" in d: return "Respiratory"
    if "gastr" in d or "gerd" in d: return "Digestive"
    if "skin" in d: return "Skin"
    return "General"

def check_vitals(hr, bp):
    if hr > 110 or bp > 140: return "CRITICAL"
    if hr > 90: return "MODERATE"
    return "NORMAL"

def predict_disease(symptoms):
    if not symptoms: return "Unknown", 0
    vec = mlb.transform([symptoms])
    probs = model.predict_proba(vec)[0]
    idx = probs.argmax()
    return model.classes_[idx], round(probs[idx]*100, 2)

def calculate_severity(symptoms):
    score = 0
    for s in symptoms:
        row = severity_df[severity_df['Symptom'] == s]
        if not row.empty:
            score += row.values[0][1]
    return score

def get_risk(score):
    if score >= 15: return "CRITICAL"
    if score >= 7: return "MODERATE"
    return "MILD"

def get_description(disease):
    row = desc_df[desc_df['Disease'] == disease]
    return row.values[0][1] if not row.empty else "No description available."

def get_precautions(disease):
    row = precaution_df[precaution_df['Disease'] == disease]
    if not row.empty:
        # Filter out 'nan' values or empty entries
        return [p for p in row.values[0][1:] if pd.notna(p) and str(p).lower() != 'nan']
    return []

def decision_engine(disease, risk, vitals):
    if risk == "CRITICAL" or vitals == "CRITICAL":
        return "⚠️ Visit a doctor immediately."
    if risk == "MODERATE":
        return "💊 Take prescribed medication and monitor closely."
    return "✅ Home care and rest should be sufficient."

# ==============================
# 5. INTERACTIVE MAIN LOOP
# ==============================
print("--- AI Health Assistant Initialized ---")

while True:
    print("\nDescribe your condition (or type 'exit'):")
    user_input = input(">> ")

    if user_input.lower() == "exit":
        break

    symptoms = extract_symptoms(user_input)

    if not symptoms:
        print("❌ No symptoms detected. Please use different words or describe more clearly.")
        continue

    # UI Improvement: Prompt for more data if only 1-2 symptoms found
    if len(symptoms) < 3:
        print(f"Detected: {symptoms}")
        print("To improve accuracy, do you have any other symptoms? (e.g., cough, fatigue, or 'no')")
        more = input(">> ")
        if more.lower() != 'no':
            symptoms = list(set(symptoms + extract_symptoms(more)))

    print("\nEnter vitals? (yes/no)")
    v_choice = input(">> ").lower()
    vitals_status = "NOT PROVIDED"
    if v_choice == "yes":
        try:
            hr = int(input("Heart Rate: "))
            bp = int(input("Systolic BP: "))
            vitals_status = check_vitals(hr, bp)
        except ValueError:
            vitals_status = "UNKNOWN (Invalid Input)"

    # Generate Report
    disease, confidence = predict_disease(symptoms)
    severity_score = calculate_severity(symptoms)
    risk_level = get_risk(severity_score)
    health_cat = get_health_type(disease)
    description = get_description(disease)
    precautions = get_precautions(disease)
    advice = decision_engine(disease, risk_level, vitals_status)

    print("\n" + "="*30)
    print("      AI HEALTH REPORT")
    print("="*30)
    print(f"Predicted Disease: {disease}")
    print(f"Confidence Level : {confidence}%")
    print(f"Health Category  : {health_cat}")
    print(f"Risk Assessment  : {risk_level}")
    print(f"Vitals Status    : {vitals_status}")
    
    if confidence < 50:
        print("\n⚠️ NOTE: Low confidence. Please provide more symptoms for a better match.")

    print(f"\n🧾 Description:\n{description}")

    if precautions:
        print("\n💊 Recommended Precautions:")
        for p in precautions:
            print(f"- {p.capitalize()}")

    print(f"\nFinal Advice: {advice}")
    print("="*30)