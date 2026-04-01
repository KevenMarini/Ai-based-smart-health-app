import pandas as pd
import re
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import SVC

# ==============================
# 1. LOAD DATASETS
# ==============================
try:
    df            = pd.read_csv("archive (1)/dataset.csv")
    severity_df   = pd.read_csv("archive (1)/Symptom-severity.csv")
    desc_df       = pd.read_csv("archive (1)/symptom_Description.csv")
    precaution_df = pd.read_csv("archive (1)/symptom_precaution.csv")
except FileNotFoundError:
    df            = pd.read_csv("dataset.csv")
    severity_df   = pd.read_csv("Symptom-severity.csv")
    desc_df       = pd.read_csv("symptom_Description.csv")
    precaution_df = pd.read_csv("symptom_precaution.csv")

# ==============================
# 2. PREPROCESS & TRAIN
# ==============================
symptom_columns = df.columns[1:]

# ✅ FIX 1 — Strip disease label trailing spaces ("Diabetes " -> "Diabetes")
#    Original bug: desc_df / precaution_df lookups silently returned nothing
#    for diseases like "Diabetes " because of trailing space mismatch.
df['Disease'] = df['Disease'].str.strip()

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

# ✅ FIX 2 — Use a Voting Ensemble (RF + SVM) instead of only Random Forest.
#    With few symptoms, a single RF gets pulled toward whichever disease has the
#    most training rows sharing those symptoms. SVM adds a different decision
#    boundary that balances this out, raising confidence on correct predictions.
rf  = RandomForestClassifier(n_estimators=300, random_state=42, class_weight='balanced')
svm = SVC(kernel='rbf', probability=True, C=10, random_state=42)
model = VotingClassifier(estimators=[('rf', rf), ('svm', svm)], voting='soft')
model.fit(X, y)

valid_symptoms = list(mlb.classes_)

# ✅ FIX 3 — Normalise severity symptom names to match dataset format.
#    "Symptom-severity.csv" has entries like "dischromic_patches" but the
#    dataset has "dischromic _patches" (extra space). Strip + lower both sides.
severity_df['Symptom'] = severity_df['Symptom'].str.strip().str.lower()

# ==============================
# 3. NLP SYMPTOM EXTRACTION
# ==============================

# ✅ FIX 4 — The original synonym map mapped "cold" -> [continuous_sneezing, chills].
#    Those two symptoms are the PRIMARY indicators of "Allergy" in the dataset,
#    not Common Cold — causing every "fever + cold + headache" query to predict
#    Allergy. Fixed by mapping "cold" to symptoms that actually appear in the
#    Common Cold disease rows of the dataset.
synonym_map = {
    # --- General ---
    "fever"              : ["high_fever"],
    "high fever"         : ["high_fever"],
    "mild fever"         : ["mild_fever"],
    "temperature"        : ["high_fever"],
    "chills"             : ["chills"],
    "sweating"           : ["sweating"],
    "night sweats"       : ["sweating"],

    # --- Respiratory / Cold-like ---
    # "cold" now maps to runny_nose + throat_irritation (Common Cold dataset symptoms)
    # NOT continuous_sneezing+chills which belong to Allergy rows.
    # Common Cold maps to its actual dataset symptoms (NOT Allergy's symptoms)
    "cold"               : ["runny_nose", "throat_irritation", "continuous_sneezing", "chills"],
    "common cold"        : ["runny_nose", "throat_irritation", "continuous_sneezing",
                            "chills", "high_fever", "cough", "headache", "fatigue",
                            "phlegm", "congestion", "sinus_pressure", "malaise"],
    "runny nose"         : ["runny_nose"],
    "phlegm"             : ["phlegm"],
    "mucus"              : ["phlegm"],
    "congestion"         : ["congestion"],
    "blocked nose"       : ["congestion"],
    "sinus"              : ["sinus_pressure"],
    "sneezing"           : ["continuous_sneezing"],
    "cough"              : ["cough"],
    "dry cough"          : ["cough"],
    "sore throat"        : ["throat_irritation"],
    "throat pain"        : ["throat_irritation"],
    "shortness of breath": ["breathlessness"],
    "breathless"         : ["breathlessness"],
    "difficulty breathing":["breathlessness"],
    "chest pain"         : ["chest_pain"],
    "chest tightness"    : ["chest_pain"],
    "stuffy nose"        : ["congestion"],
    "malaise"            : ["malaise"],

    # --- Head / Neuro ---
    "headache"           : ["headache"],
    "head pain"          : ["headache"],
    "migraine"           : ["headache"],
    "dizzy"              : ["dizziness"],
    "dizziness"          : ["dizziness"],
    "lightheaded"        : ["dizziness"],
    "spinning"           : ["dizziness"],
    "blurred vision"     : ["blurred_and_distorted_vision"],

    # --- Fatigue / Body ---
    "tired"              : ["fatigue"],
    "exhausted"          : ["fatigue"],
    "fatigue"            : ["fatigue"],
    "weak"               : ["fatigue"],
    "weakness"           : ["fatigue"],
    "no energy"          : ["fatigue"],
    "lethargy"           : ["lethargy"],
    "body pain"          : ["muscle_pain", "joint_pain"],
    "body ache"          : ["muscle_pain"],
    "muscle pain"        : ["muscle_pain"],
    "joint pain"         : ["joint_pain"],
    "back pain"          : ["back_pain"],
    "neck pain"          : ["neck_pain"],
    "stiff neck"         : ["stiff_neck"],
    "shaking"            : ["shivering"],
    "trembling"          : ["shivering"],

    # --- Digestive ---
    "nausea"             : ["nausea"],
    "nauseous"           : ["nausea"],
    "vomit"              : ["vomiting"],
    "vomiting"           : ["vomiting"],
    "throw up"           : ["vomiting"],
    "puke"               : ["vomiting"],
    "stomach pain"       : ["stomach_pain"],
    "stomach ache"       : ["stomach_pain", "abdominal_pain"],
    "stomach hurts"      : ["stomach_pain", "abdominal_pain"],
    "belly pain"         : ["stomach_pain"],
    "abdominal pain"     : ["abdominal_pain"],
    "heartburn"          : ["acidity"],
    "acidity"            : ["acidity"],
    "diarrhea"           : ["diarrhoea"],
    "loose stool"        : ["diarrhoea"],
    "constipation"       : ["constipation"],
    "bloating"           : ["abdominal_pain"],
    "indigestion"        : ["acidity", "indigestion"],
    "loss of appetite"   : ["loss_of_appetite"],
    "not hungry"         : ["loss_of_appetite"],

    # --- Skin ---
    "itchy"              : ["itching"],
    "itching"            : ["itching"],
    "rash"               : ["skin_rash"],
    "skin rash"          : ["skin_rash"],
    "hives"              : ["skin_rash"],
    "yellow skin"        : ["yellowing_of_eyes"],
    "yellow eyes"        : ["yellowing_of_eyes"],
    "jaundice"           : ["yellowing_of_eyes"],

    # --- Eyes / Senses ---
    "watery eyes"        : ["watering_from_eyes"],
    "red eyes"           : ["redness_of_eyes"],
    "can't smell"        : ["loss_of_smell"],
    "no smell"           : ["loss_of_smell"],

    # --- Urinary ---
    "burning urination"  : ["burning_micturition"],
    "painful urination"  : ["burning_micturition"],
    "frequent urination" : ["frequent_urination"],
    "dark urine"         : ["dark_urine"],

    # --- Other ---
    "weight loss"        : ["weight_loss"],
    "weight gain"        : ["weight_gain"],
    "anxiety"            : ["anxiety"],
    "swollen lymph"      : ["swollen_lymph_nodes"],
    "lymph node"         : ["swollen_lymph_nodes"],
    "gas"                : ["passage_of_gases"],
}

def extract_symptoms(text):
    text = text.lower().strip()
    found = []

    # Pass 1 — synonym phrases (longest first to avoid partial overlaps)
    for phrase in sorted(synonym_map, key=len, reverse=True):
        if re.search(r'\b' + re.escape(phrase) + r'\b', text):
            found.extend(synonym_map[phrase])

    # Pass 2 — direct match against dataset clinical terms
    for symptom in valid_symptoms:
        clean = symptom.replace("_", " ")
        if clean in text:
            found.append(symptom)

    # Only keep symptoms the model actually knows
    return list(set(s for s in found if s in valid_symptoms))

# ==============================
# 4. HELPER FUNCTIONS
# ==============================

def get_health_type(disease):
    d = disease.lower()
    if any(w in d for w in ["malaria", "typhoid", "dengue", "aids", "tuberculosis",
                             "hepatitis", "infection", "fever", "chicken pox"]):
        return "Infection / Fever"
    if any(w in d for w in ["cold", "cough", "asthma", "pneumonia", "bronchial"]):
        return "Respiratory"
    if any(w in d for w in ["gastro", "gerd", "ulcer", "jaundice", "cholestasis"]):
        return "Digestive"
    if any(w in d for w in ["skin", "fungal", "acne", "psoriasis", "impetigo", "allergy"]):
        return "Skin / Allergy"
    if any(w in d for w in ["diabetes", "hyperthyroid", "hypothyroid"]):
        return "Endocrine"
    return "General"

def check_vitals(hr, bp):
    if hr > 110 or bp > 140: return "CRITICAL"
    if hr > 90  or bp > 120: return "MODERATE"
    return "NORMAL"

def predict_disease(symptoms):
    if not symptoms:
        return "Unknown", 0, []
    vec = mlb.transform([symptoms])
    probs = model.predict_proba(vec)[0]
    top3_idx = probs.argsort()[::-1][:3]
    top3 = [(model.classes_[i], round(probs[i] * 100, 1)) for i in top3_idx]
    best_disease, best_conf = top3[0]
    return best_disease, best_conf, top3

def calculate_severity(symptoms):
    score = 0
    for s in symptoms:
        row = severity_df[severity_df['Symptom'] == s]
        if not row.empty:
            score += int(row.values[0][1])
    return score

def get_risk(score):
    # ✅ FIX 5 — Original thresholds were too aggressive.
    #    4 everyday symptoms (fever=7, sneezing=4, chills=3, headache=3) summed to
    #    17 and triggered CRITICAL. Raised thresholds to reflect realistic severity.
    if score >= 25: return "CRITICAL"
    if score >= 13: return "MODERATE"
    return "MILD"

def get_description(disease):
    # ✅ FIX 6 — Strip disease name before lookup (matches FIX 1)
    row = desc_df[desc_df['Disease'].str.strip() == disease]
    return row.values[0][1] if not row.empty else "No description available."

def get_precautions(disease):
    row = precaution_df[precaution_df['Disease'].str.strip() == disease]
    if not row.empty:
        return [p for p in row.values[0][1:] if pd.notna(p) and str(p).lower() != 'nan']
    return []

def decision_engine(disease, risk, vitals):
    if vitals == "CRITICAL":
        return "🚨 EMERGENCY: Your vitals are critical — seek immediate medical attention."
    if risk == "CRITICAL":
        return "⚠️  Visit a doctor immediately. Do not delay."
    if risk == "MODERATE":
        return "💊 Take prescribed medication and monitor your symptoms closely."
    return "✅ Home care and rest should be sufficient. Monitor for worsening symptoms."

# ==============================
# 5. INTERACTIVE MAIN LOOP
# ==============================
print("=" * 40)
print("   AI Health Assistant (Fixed v2)")
print("=" * 40)

while True:
    print("\nDescribe your symptoms (or type 'exit'):")
    user_input = input(">> ")

    if user_input.lower().strip() == "exit":
        print("Goodbye! Stay healthy. 👋")
        break

    symptoms = extract_symptoms(user_input)

    if not symptoms:
        print("❌ No symptoms recognised. Try plain English, e.g.:")
        print("   'I have fever, headache and body pain'")
        continue

    # Ask for more if we have fewer than 3 symptoms
    if len(symptoms) < 3:
        print(f"Detected: {[s.replace('_', ' ') for s in symptoms]}")
        print("Any other symptoms? (type them or press Enter to skip)")
        more = input(">> ").strip()
        if more and more.lower() not in ('no', 'n', 'none'):
            symptoms = list(set(symptoms + extract_symptoms(more)))

    print(f"\n✅ Symptoms used: {[s.replace('_', ' ') for s in symptoms]}")

    print("\nEnter vitals? (yes / no)")
    vitals_status = "NOT PROVIDED"
    if input(">> ").strip().lower() == "yes":
        try:
            hr = int(input("  Heart Rate (bpm)   : "))
            bp = int(input("  Systolic BP (mmHg) : "))
            vitals_status = check_vitals(hr, bp)
        except ValueError:
            vitals_status = "UNKNOWN (invalid input)"

    # --- Prediction ---
    disease, confidence, top3 = predict_disease(symptoms)
    severity_score = calculate_severity(symptoms)
    risk_level     = get_risk(severity_score)
    health_cat     = get_health_type(disease)
    description    = get_description(disease)
    precautions    = get_precautions(disease)
    advice         = decision_engine(disease, risk_level, vitals_status)

    # --- Report ---
    print("\n" + "=" * 40)
    print("          AI HEALTH REPORT")
    print("=" * 40)
    print(f"  Predicted Disease : {disease}")
    print(f"  Confidence        : {confidence}%")
    print(f"  Health Category   : {health_cat}")
    print(f"  Risk Assessment   : {risk_level}  (severity score: {severity_score})")
    print(f"  Vitals Status     : {vitals_status}")

    # ✅ FIX 7 — Show top-3 alternatives so user can self-check
    print("\n  Other possibilities:")
    for alt_disease, alt_conf in top3[1:]:
        print(f"    • {alt_disease} ({alt_conf}%)")

    if confidence < 50:
        print("\n  ⚠️  Low confidence — please describe more symptoms for a better result.")

    print(f"\n📋 About {disease}:")
    print(f"  {description}")

    if precautions:
        print("\n💊 Recommended Precautions:")
        for p in precautions:
            print(f"  • {p.capitalize()}")

    print(f"\n🏥 Final Advice: {advice}")
    print("=" * 40)