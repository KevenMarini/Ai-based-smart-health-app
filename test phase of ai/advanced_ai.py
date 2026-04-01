import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.ensemble import RandomForestClassifier
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
# TRAIN MODEL
# ==============================

mlb = MultiLabelBinarizer()
X = mlb.fit_transform(df['symptoms'])
y = df['Disease']

model = RandomForestClassifier(n_estimators=300, random_state=42)
model.fit(X, y)

valid_symptoms = list(mlb.classes_)

# ==============================
# 🔥 SMART NLP (SCORING BASED)
# ==============================

def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

def extract_symptoms(text):
    text = text.lower()
    found = []

    # Reliable keyword mapping
    if "cold" in text:
        found.append("continuous_sneezing")
    if "fever" in text:
        found.append("high_fever")
    if "headache" in text:
        found.append("headache")

    words = text.split()

    for word in words:
        best_match = None
        best_score = 0

        for symptom in valid_symptoms:
            clean = symptom.replace("_", " ")
            score = similarity(word, clean)

            if word in clean:
                score += 0.5

            if score > best_score:
                best_score = score
                best_match = symptom

        if best_score > 0.6:
            found.append(best_match)

    # Keep only valid symptoms
    found = [s for s in found if s in valid_symptoms]

    return list(set(found))

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
# ML PREDICTION
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

    if confidence < 40:
        print("⚠️ Low confidence → Add more symptoms")

    print("\n🧾 Description:")
    print(desc)

    print("\n💊 Precautions:")
    for p in precautions:
        print("-", p)

    print("\nDecision:")
    print(decision)