import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.ensemble import GradientBoostingClassifier
from difflib import SequenceMatcher

# ==============================
# LOAD DATASETS
# ==============================

df = pd.read_csv("archive (1)/dataset.csv")
severity_df = pd.read_csv("archive (1)/Symptom-severity.csv")
desc_df = pd.read_csv("archive (1)/symptom_Description.csv")
precaution_df = pd.read_csv("archive (1)/symptom_precaution.csv")

# ==============================
# PREPROCESS
# ==============================

symptom_columns = df.columns[1:]

def combine_symptoms(row):
    symptoms = []
    for col in symptom_columns:
        if pd.notna(row[col]):
            symptoms.append(str(row[col]).strip().lower())
    return symptoms

df['symptoms'] = df.apply(combine_symptoms, axis=1)

# ==============================
# TRAIN MODEL (UPGRADED)
# ==============================

mlb = MultiLabelBinarizer()
X = mlb.fit_transform(df['symptoms'])
y = df['Disease']

model = GradientBoostingClassifier()
model.fit(X, y)

valid_symptoms = list(mlb.classes_)

# ==============================
# 🔥 HIGH-ACCURACY NLP
# ==============================

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def extract_symptoms(text):
    text = text.lower()
    scores = []

    for symptom in valid_symptoms:
        clean = symptom.replace("_", " ")

        score = similarity(text, clean)

        # boost if words match
        for word in text.split():
            if word in clean:
                score += 0.2

        scores.append((symptom, score))

    # sort best matches
    scores = sorted(scores, key=lambda x: x[1], reverse=True)

    # take TOP 3 only
    top_symptoms = [s[0] for s in scores[:3] if s[1] > 0.4]

    return top_symptoms

# ==============================
# HEALTH TYPE
# ==============================

def get_health_type(disease):
    d = disease.lower()

    if "fever" in d or "infection" in d:
        return "Infection"
    elif "cold" in d or "cough" in d:
        return "Respiratory"
    elif "gastr" in d or "gerd" in d:
        return "Digestive"
    elif "skin" in d:
        return "Skin"
    return "General"

# ==============================
# VITALS (OPTIONAL)
# ==============================

def check_vitals(hr, bp):
    if hr > 110 or bp > 140:
        return "CRITICAL"
    elif hr > 90:
        return "MODERATE"
    return "NORMAL"

# ==============================
# PREDICTION
# ==============================

def predict_disease(symptoms):
    if not symptoms:
        return "Unknown", 0

    vec = mlb.transform([symptoms])
    probs = model.predict_proba(vec)[0]

    idx = probs.argmax()
    return model.classes_[idx], round(probs[idx]*100, 2)

# ==============================
# SEVERITY
# ==============================

def calculate_severity(symptoms):
    score = 0
    for s in symptoms:
        row = severity_df[severity_df['Symptom'] == s]
        if not row.empty:
            score += row.values[0][1]
    return score

def get_risk(score):
    if score >= 15:
        return "CRITICAL"
    elif score >= 7:
        return "MODERATE"
    return "MILD"

# ==============================
# DESCRIPTION + PRECAUTIONS
# ==============================

def get_description(disease):
    row = desc_df[desc_df['Disease'] == disease]
    return row.values[0][1] if not row.empty else "No description"

def get_precautions(disease):
    row = precaution_df[precaution_df['Disease'] == disease]
    return list(row.values[0][1:]) if not row.empty else []

# ==============================
# DECISION ENGINE
# ==============================

def decision_engine(disease, risk, vitals):

    if risk == "CRITICAL" or vitals == "CRITICAL":
        return "⚠️ Visit doctor immediately"

    if risk == "MODERATE":
        return "💊 Take medication and monitor"

    return "✅ Home care sufficient"

# ==============================
# MAIN LOOP
# ==============================

while True:
    print("\nDescribe your condition (or type exit):")
    text = input(">> ")

    if text.lower() == "exit":
        break

    symptoms = extract_symptoms(text)

    if not symptoms:
        print("❌ No symptoms detected")
        continue

    print("Detected Symptoms:", symptoms)

    print("\nEnter vitals? (yes/no)")
    v = input(">> ").lower()

    if v == "yes":
        try:
            hr = int(input("Heart Rate: "))
            bp = int(input("BP: "))
            vitals = check_vitals(hr, bp)
        except:
            vitals = "UNKNOWN"
    else:
        vitals = "NOT PROVIDED"

    disease, confidence = predict_disease(symptoms)
    severity = calculate_severity(symptoms)
    risk = get_risk(severity)
    health_type = get_health_type(disease)

    desc = get_description(disease)
    precautions = get_precautions(disease)

    decision = decision_engine(disease, risk, vitals)

    print("\n===== AI HEALTH REPORT =====")
    print("Health Type:", health_type)
    print("Disease:", disease)
    print("Confidence:", confidence, "%")
    print("Risk:", risk)
    print("Vitals:", vitals)

    if confidence < 30:
        print("⚠️ Prediction not reliable → add more symptoms")

    print("\n🧾 Description:")
    print(desc)

    print("\n💊 Precautions:")
    for p in precautions:
        print("-", p)

    print("\nDecision:")
    print(decision)