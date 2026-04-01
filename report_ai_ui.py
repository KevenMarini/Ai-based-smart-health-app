"""
OCR-Powered AI Health Assistant
Dito copy of test1_ui.py with added OCR extraction for medical reports.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading, time, re, sys, os, json
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.ensemble import RandomForestClassifier

# Import your OCR module
import step1_ocr

# ── colour palette ──────────────────────────────────────────────────
BG           = "#0f1117"
PANEL_BG     = "#1a1d27"
CARD_BG      = "#232734"
ACCENT       = "#6c63ff"
ACCENT_HOVER = "#857dff"
SUCCESS      = "#00c896"
WARNING      = "#ffb347"
DANGER       = "#ff5c5c"
TEXT         = "#e8eaed"
TEXT_DIM     = "#8b8fa3"
BORDER       = "#2e3348"

FONT_TITLE   = ("Segoe UI", 22, "bold")
FONT_HEAD    = ("Segoe UI", 13, "bold")
FONT_BODY    = ("Segoe UI", 11)
FONT_SMALL   = ("Segoe UI", 10)
FONT_MONO    = ("Consolas", 11)
FONT_BIG     = ("Segoe UI", 15, "bold")

# ══════════════════════════════════════════════════════════════════════
#  BACKEND — logic from test1.py
# ══════════════════════════════════════════════════════════════════════

def _load_data():
    try:
        df = pd.read_csv("archive (1)/dataset.csv")
        severity_df = pd.read_csv("archive (1)/Symptom-severity.csv")
        desc_df = pd.read_csv("archive (1)/symptom_Description.csv")
        precaution_df = pd.read_csv("archive (1)/symptom_precaution.csv")
    except FileNotFoundError:
        df = pd.read_csv("dataset.csv")
        severity_df = pd.read_csv("Symptom-severity.csv")
        desc_df = pd.read_csv("symptom_Description.csv")
        precaution_df = pd.read_csv("symptom_precaution.csv")

    symptom_columns = df.columns[1:]
    def combine_symptoms(row):
        s = []; [s.append(str(row[col]).strip().lower()) for col in symptom_columns if pd.notna(row[col])]
        return s

    df['symptoms'] = df.apply(combine_symptoms, axis=1)
    mlb = MultiLabelBinarizer()
    X = mlb.fit_transform(df['symptoms'])
    y = df['Disease']
    model = RandomForestClassifier(n_estimators=300, random_state=42)
    model.fit(X, y)
    valid_symptoms = list(mlb.classes_)
    return model, mlb, valid_symptoms, severity_df, desc_df, precaution_df, df['Disease'].unique()

def extract_symptoms(text, valid_symptoms):
    text = text.lower()
    found = []
    synonym_map = {
        "cold": ["continuous_sneezing", "chills"], "fever": ["high_fever"],
        "throw up": ["vomiting"], "puke": ["vomiting"], "tired": ["fatigue"],
        "exhausted": ["fatigue"], "dizzy": ["dizziness"], "headache": ["headache"]
    }
    for p, mp in synonym_map.items():
        if re.search(r'\b' + re.escape(p) + r'\b', text): found.extend(mp)
    for s in valid_symptoms:
        if s.replace("_", " ") in text: found.append(s)
    return list(set(found))

def get_health_type(disease):
    d = disease.lower()
    if "fever" in d or "infection" in d: return "Infection"
    if "cold" in d or "cough" in d: return "Respiratory"
    return "General"

def predict_disease(symptoms, model, mlb):
    if not symptoms: return "Unknown", 0
    X_input = mlb.transform([symptoms])
    probs = model.predict_proba(X_input)[0]
    idx = probs.argmax()
    return model.classes_[idx], round(probs[idx] * 100, 2)

def calculate_severity(symptoms, severity_df):
    score = 0
    for s in symptoms:
        row = severity_df[severity_df['Symptom'] == s]
        if not row.empty: score += row.values[0][1]
    return score

def get_risk(score):
    if score >= 15: return "CRITICAL"; return "MODERATE" if score >= 7 else "MILD"

def get_description(disease, desc_df):
    r = desc_df[desc_df['Disease'] == disease]
    return r.values[0][1] if not r.empty else "N/A"

def get_precautions(disease, precaution_df):
    r = precaution_df[precaution_df['Disease'] == disease]
    return [p for p in r.values[0][1:] if pd.notna(p) and str(p).lower() != 'nan'] if not r.empty else []

def decision_engine(disease, risk, vitals, mentioned_disease=None):
    if mentioned_disease and mentioned_disease.lower() == disease.lower():
        prefix = f"⚠️ Report confirms suspected {disease}. "
    elif mentioned_disease:
        prefix = f"💡 Report suggests {mentioned_disease}, though symptoms match {disease}. "
    else:
        prefix = ""
        
    if risk == "CRITICAL" or vitals == "CRITICAL":
        return prefix + "Visit a doctor immediately."
    return prefix + "Home care and rest should be sufficient."

# ══════════════════════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════════════════════

class ReportAIApp(tk.Tk):
    def __init__(self, user_email=None, image_path=None):
        super().__init__()
        self.user_email = user_email
        self.image_path = image_path
        self.mentioned_disease = None
        
        self.title("AI Medical Report Analyzer")
        self.configure(bg=BG)
        self.geometry("1100x850")
        
        self._show_loading()
        threading.Thread(target=self._init_data, daemon=True).start()
        self._poll_data()

    def _init_data(self):
        self.model, self.mlb, self.valid_symptoms, self.severity_df, \
            self.desc_df, self.precaution_df, self.all_diseases = _load_data()
        
        # OCR Extraction if image provided
        self.ocr_results = {"symptoms": [], "hr": "", "bp": "", "disease": None}
        if self.image_path and os.path.exists(self.image_path):
            text = step1_ocr.extract_text(self.image_path)
            self._parse_ocr(text)
            
        self._data_ready = True

    def _parse_ocr(self, text):
        text_lower = text.lower()
        # Find Vitals
        hr_match = re.search(r'\b(?:hr|heart rate|pulse)[:\s]*(\d+)', text_lower)
        if hr_match: self.ocr_results["hr"] = hr_match.group(1)
        
        bp_match = re.search(r'\b(?:bp|blood pressure)[:\s]*(\d+/\d+)', text_lower)
        if bp_match: self.ocr_results["bp"] = bp_match.group(1)
        
        # Find Symptoms
        self.ocr_results["symptoms"] = extract_symptoms(text, self.valid_symptoms)
        
        # Find Mentioned Disease
        for d in self.all_diseases:
            if d.lower() in text_lower:
                self.ocr_results["disease"] = d
                self.mentioned_disease = d
                break

    def _show_loading(self):
        self.load_frame = tk.Frame(self, bg=BG)
        self.load_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        tk.Label(self.load_frame, text="🩺", font=("Segoe UI", 48), bg=BG, fg=ACCENT).pack(pady=(200, 10))
        tk.Label(self.load_frame, text="Analyzing Medical Report...", font=FONT_TITLE, bg=BG, fg=TEXT).pack()
        self._data_ready = False

    def _poll_data(self):
        if self._data_ready:
            self.load_frame.destroy()
            self._build_ui()
            self._populate_ocr()
        else:
            self.after(200, self._poll_data)

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=PANEL_BG, height=60)
        header.pack(fill="x")
        tk.Label(header, text="📑  Report-Based AI Analysis", font=FONT_TITLE, bg=PANEL_BG, fg=TEXT).pack(side="left", padx=20)
        
        body = tk.Frame(self, bg=BG); body.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Original Left Panel
        left = tk.Frame(body, bg=PANEL_BG, width=400, highlightbackground=BORDER, highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 15))
        left.pack_propagate(False)
        
        tk.Label(left, text="Extracted Findings", font=FONT_HEAD, bg=PANEL_BG, fg=TEXT).pack(anchor="w", padx=16, pady=15)
        
        self.symptom_text = tk.Text(left, height=8, font=FONT_BODY, bg=CARD_BG, fg=TEXT, bd=0, padx=10, pady=10)
        self.symptom_text.pack(fill="x", padx=16, pady=5)
        
        tk.Label(left, text="Vitals from Report", font=FONT_HEAD, bg=PANEL_BG, fg=TEXT).pack(anchor="w", padx=16, pady=(15, 5))
        vf = tk.Frame(left, bg=PANEL_BG); vf.pack(fill="x", padx=16)
        tk.Label(vf, text="Heart Rate", font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).grid(row=0, column=0, sticky="w")
        self.hr_entry = self._styled_entry(vf); self.hr_entry.grid(row=0, column=1, pady=5, padx=10)
        tk.Label(vf, text="Blood Pressure", font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).grid(row=1, column=0, sticky="w")
        self.bp_entry = self._styled_entry(vf); self.bp_entry.grid(row=1, column=1, pady=5, padx=10)
        
        self.tag_frame = tk.Frame(left, bg=PANEL_BG); self.tag_frame.pack(fill="x", padx=16, pady=20)
        
        tk.Button(left, text="🔍 Run AI Analysis", font=FONT_HEAD, bg=ACCENT, fg="white", command=self._on_analyse, pady=10).pack(fill="x", padx=16, pady=20)

        # Right Panel
        self.report_area = tk.Frame(body, bg=PANEL_BG, highlightbackground=BORDER, highlightthickness=1)
        self.report_area.pack(side="left", fill="both", expand=True)
        tk.Label(self.report_area, text="Health Interpretation", font=FONT_TITLE, bg=PANEL_BG, fg=TEXT).pack(pady=100)

    def _styled_entry(self, parent):
        return tk.Entry(parent, font=FONT_BODY, bg=CARD_BG, fg=TEXT, insertbackground=TEXT, bd=0, highlightthickness=1)

    def _populate_ocr(self):
        if self.ocr_results["hr"]: self.hr_entry.insert(0, self.ocr_results["hr"])
        if self.ocr_results["bp"]: self.bp_entry.insert(0, self.ocr_results["bp"])
        
        sym_str = ", ".join([s.replace("_", " ") for s in self.ocr_results["symptoms"]])
        if self.ocr_results["disease"]:
            sym_str = f"[Suspected Diagnosis: {self.ocr_results['disease']}]\n" + sym_str
            
        self.symptom_text.insert("1.0", sym_str)

    def _on_analyse(self):
        raw = self.symptom_text.get("1.0", "end").strip()
        syms = extract_symptoms(raw, self.valid_symptoms)
        
        disease, conf = predict_disease(syms, self.model, self.mlb)
        score = calculate_severity(syms, self.severity_df)
        risk = get_risk(score)
        
        # Account for mentioned disease in logic
        advice = decision_engine(disease, risk, "NORMAL", self.mentioned_disease)
        self._render_report(disease, conf, risk, advice)

    def _render_report(self, disease, confidence, risk, advice):
        for w in self.report_area.winfo_children(): w.destroy()
        inner = tk.Frame(self.report_area, bg=PANEL_BG, padx=30, pady=30); inner.pack(fill="both", expand=True)
        
        tk.Label(inner, text="AI Analysis Result", font=FONT_TITLE, bg=PANEL_BG, fg=ACCENT).pack(anchor="w")
        
        f = tk.Frame(inner, bg=CARD_BG, padx=20, pady=20, highlightthickness=1); f.pack(fill="x", pady=20)
        tk.Label(f, text=f"Predicted Condition: {disease}", font=FONT_BIG, bg=CARD_BG, fg=TEXT).pack(anchor="w")
        tk.Label(f, text=f"Confidence: {confidence}%", font=FONT_HEAD, bg=CARD_BG, fg=SUCCESS).pack(anchor="w")
        tk.Label(f, text=f"Risk Level: {risk}", font=FONT_HEAD, bg=CARD_BG, fg=WARNING).pack(anchor="w", pady=10)
        
        adv_f = tk.Frame(inner, bg=DANGER if risk=="CRITICAL" else SUCCESS, padx=15, pady=15)
        adv_f.pack(fill="x")
        tk.Label(adv_f, text=advice, font=FONT_HEAD, bg=adv_f["bg"], fg="white", wraplength=500).pack()

if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else None
    app = ReportAIApp(image_path=path); app.mainloop()
