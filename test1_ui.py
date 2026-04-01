"""
AI Health Assistant — Professional Tkinter UI
Wraps the logic of test1.py into a modern, dark-themed medical dashboard.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading, time, re
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.ensemble import RandomForestClassifier

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
#  BACKEND — identical logic from test1.py
# ══════════════════════════════════════════════════════════════════════

def _load_data():
    """Load CSVs and train the model (runs once at startup)."""
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
    return model, mlb, valid_symptoms, severity_df, desc_df, precaution_df

def extract_symptoms(text, valid_symptoms):
    text = text.lower()
    found = []
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
        "shaking": ["shivering"],
    }
    for phrase, mapped in synonym_map.items():
        if re.search(r'\b' + re.escape(phrase) + r'\b', text):
            found.extend(mapped)
    for symptom in valid_symptoms:
        if symptom.replace("_", " ") in text:
            found.append(symptom)
    return list(set(found))

def get_health_type(disease):
    d = disease.lower()
    if "fever" in d or "infection" in d: return "Infection"
    if "cold" in d or "cough" in d:      return "Respiratory"
    if "gastr" in d or "gerd" in d:      return "Digestive"
    if "skin" in d:                       return "Skin"
    return "General"

def check_vitals(hr, bp):
    if hr > 110 or bp > 140: return "CRITICAL"
    if hr > 90:              return "MODERATE"
    return "NORMAL"

def predict_disease(symptoms, model, mlb):
    if not symptoms:
        return "Unknown", 0
    vec = mlb.transform([symptoms])
    probs = model.predict_proba(vec)[0]
    idx = probs.argmax()
    return model.classes_[idx], round(probs[idx] * 100, 2)

def calculate_severity(symptoms, severity_df):
    score = 0
    for s in symptoms:
        row = severity_df[severity_df['Symptom'] == s]
        if not row.empty:
            score += row.values[0][1]
    return score

def get_risk(score):
    if score >= 15: return "CRITICAL"
    if score >= 7:  return "MODERATE"
    return "MILD"

def get_description(disease, desc_df):
    row = desc_df[desc_df['Disease'] == disease]
    return row.values[0][1] if not row.empty else "No description available."

def get_description(disease, desc_df):
    row = desc_df[desc_df['Disease'] == disease]
    return row.values[0][1] if not row.empty else "No description available."

def get_precautions(disease, precaution_df):
    row = precaution_df[precaution_df['Disease'] == disease]
    if not row.empty:
        return [p for p in row.values[0][1:] if pd.notna(p) and str(p).lower() != 'nan']
    return []

def decision_engine(disease, risk, vitals):
    if risk == "CRITICAL" or vitals == "CRITICAL":
        return "⚠️  Visit a doctor immediately."
    if risk == "MODERATE":
        return "💊  Take prescribed medication and monitor closely."
    return "✅  Home care and rest should be sufficient."

# ══════════════════════════════════════════════════════════════════════
#  GUI
# ══════════════════════════════════════════════════════════════════════

class HealthApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Health Assistant")
        self.configure(bg=BG)
        self.geometry("1060x780")
        self.minsize(900, 680)

        self._show_loading()
        self.update()

        self._model_ready = False
        threading.Thread(target=self._init_model, daemon=True).start()
        self._poll_model()

    def _show_loading(self):
        self.load_frame = tk.Frame(self, bg=BG)
        self.load_frame.place(relx=0, rely=0, relwidth=1, relheight=1)

        tk.Label(self.load_frame, text="🩺", font=("Segoe UI Emoji", 48),
                 bg=BG, fg=ACCENT).pack(pady=(180, 10))
        tk.Label(self.load_frame, text="AI Health Assistant",
                 font=FONT_TITLE, bg=BG, fg=TEXT).pack()
        self._load_label = tk.Label(self.load_frame,
                                     text="Training model — please wait …",
                                     font=FONT_BODY, bg=BG, fg=TEXT_DIM)
        self._load_label.pack(pady=8)

        self._bar_canvas = tk.Canvas(self.load_frame, width=320, height=6,
                                      bg=PANEL_BG, highlightthickness=0)
        self._bar_canvas.pack(pady=10)
        self._bar_pos = 0
        self._animate_bar()

    def _animate_bar(self):
        if not hasattr(self, '_bar_canvas') or not self._bar_canvas.winfo_exists():
            return
        self._bar_canvas.delete("all")
        w = 320
        x = self._bar_pos % (w + 80) - 80
        self._bar_canvas.create_rectangle(max(x, 0), 0, min(x + 80, w), 6,
                                           fill=ACCENT, outline="")
        self._bar_pos += 4
        self.after(30, self._animate_bar)

    def _init_model(self):
        self.model, self.mlb, self.valid_symptoms, \
            self.severity_df, self.desc_df, self.precaution_df = _load_data()
        self._model_ready = True

    def _poll_model(self):
        if self._model_ready:
            self.load_frame.destroy()
            self._build_ui()
        else:
            self.after(200, self._poll_model)

    def _build_ui(self):
        header = tk.Frame(self, bg=PANEL_BG, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        tk.Label(header, text="🩺  AI Health Assistant", font=FONT_TITLE,
                 bg=PANEL_BG, fg=TEXT).pack(side="left", padx=20)
        tk.Label(header, text="Powered by RandomForest + NLP",
                 font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM).pack(side="right", padx=20)

        tk.Frame(self, bg=ACCENT, height=3).pack(fill="x")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        # LEFT panel
        left = tk.Frame(body, bg=PANEL_BG, width=380, bd=0,
                        highlightbackground=BORDER, highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)

        self._section(left, "Describe Your Symptoms")
        # FIXED: Removed comma syntax error in Label
        tk.Label(left, text="Type naturally, e.g. I have a headache and I feel tired",
                 font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM,
                 justify="left").pack(anchor="w", padx=16, pady=(0, 6))

        self.symptom_text = tk.Text(left, height=6, wrap="word",
                                     font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                                     insertbackground=TEXT, bd=0,
                                     highlightbackground=BORDER,
                                     highlightthickness=1, padx=10, pady=8)
        self.symptom_text.pack(fill="x", padx=16, pady=(0, 12))

        self._section(left, "Vitals  (optional)")
        vf = tk.Frame(left, bg=PANEL_BG)
        vf.pack(fill="x", padx=16, pady=(0, 6))

        tk.Label(vf, text="Heart Rate (bpm)", font=FONT_SMALL,
                 bg=PANEL_BG, fg=TEXT_DIM).grid(row=0, column=0, sticky="w")
        self.hr_entry = self._styled_entry(vf)
        self.hr_entry.grid(row=0, column=1, padx=(8, 0), pady=3, sticky="ew")

        tk.Label(vf, text="Systolic BP", font=FONT_SMALL,
                 bg=PANEL_BG, fg=TEXT_DIM).grid(row=1, column=0, sticky="w")
        self.bp_entry = self._styled_entry(vf)
        self.bp_entry.grid(row=1, column=1, padx=(8, 0), pady=3, sticky="ew")
        vf.columnconfigure(1, weight=1)

        self._section(left, "Detected Symptoms")
        self.tag_frame = tk.Frame(left, bg=PANEL_BG)
        self.tag_frame.pack(fill="x", padx=16, pady=(0, 12))
        self._no_sym_label = tk.Label(self.tag_frame,
                                       text="Symptoms will appear here after analysis",
                                       font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM)
        self._no_sym_label.pack(anchor="w")

        bf = tk.Frame(left, bg=PANEL_BG)
        bf.pack(fill="x", padx=16, pady=(0, 16))
        self.analyze_btn = self._accent_button(bf, "🔍  Analyse", self._on_analyse)
        self.analyze_btn.pack(fill="x", pady=(0, 6))
        self._clear_btn = self._ghost_button(bf, "Clear", self._on_clear)
        self._clear_btn.pack(fill="x")

        # RIGHT panel
        right = tk.Frame(body, bg=PANEL_BG, bd=0,
                         highlightbackground=BORDER, highlightthickness=1)
        right.pack(side="left", fill="both", expand=True)

        self._section(right, "Health Report")

        self.report_area = tk.Frame(right, bg=PANEL_BG)
        self.report_area.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self._placeholder = tk.Label(
            self.report_area,
            text="Your health report will appear here.\n\n"
                 "Describe your symptoms on the left\nand click  🔍 Analyse.",
            font=FONT_BODY, bg=PANEL_BG, fg=TEXT_DIM, justify="center")
        self._placeholder.pack(expand=True)

        ft = tk.Frame(self, bg=PANEL_BG, height=32)
        ft.pack(fill="x", side="bottom")
        ft.pack_propagate(False)
        tk.Label(ft, text="⚕️  Disclaimer: This is an AI tool — not a substitute for professional medical advice.",
                 font=("Segoe UI", 9), bg=PANEL_BG, fg=TEXT_DIM).pack(side="left", padx=16)

    def _section(self, parent, title):
        tk.Label(parent, text=title, font=FONT_HEAD,
                 bg=PANEL_BG, fg=TEXT).pack(anchor="w", padx=16, pady=(14, 4))

    def _styled_entry(self, parent):
        e = tk.Entry(parent, font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                     insertbackground=TEXT, bd=0, highlightbackground=BORDER,
                     highlightthickness=1)
        return e

    def _accent_button(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, font=FONT_HEAD, bg=ACCENT,
                        fg="white", activebackground=ACCENT_HOVER,
                        activeforeground="white", bd=0, cursor="hand2",
                        command=cmd, pady=8)
        btn.bind("<Enter>", lambda e: btn.configure(bg=ACCENT_HOVER))
        btn.bind("<Leave>", lambda e: btn.configure(bg=ACCENT))
        return btn

    def _ghost_button(self, parent, text, cmd):
        btn = tk.Button(parent, text=text, font=FONT_BODY, bg=PANEL_BG,
                        fg=TEXT_DIM, activebackground=CARD_BG,
                        activeforeground=TEXT, bd=0, cursor="hand2",
                        command=cmd, pady=4,
                        highlightbackground=BORDER, highlightthickness=1)
        return btn

    def _on_analyse(self):
        raw = self.symptom_text.get("1.0", "end").strip()
        if not raw:
            messagebox.showwarning("No input", "Please describe your symptoms first.")
            return

        symptoms = extract_symptoms(raw, self.valid_symptoms)
        if not symptoms:
            messagebox.showinfo("No Symptoms Found",
                                "Could not detect any symptoms.\n"
                                "Try using different words, e.g.:\n"
                                " • 'I have a headache and feel tired'\n"
                                " • 'fever, cough, muscle pain'")
            return

        for w in self.tag_frame.winfo_children():
            w.destroy()
        row_frame = tk.Frame(self.tag_frame, bg=PANEL_BG)
        row_frame.pack(anchor="w", fill="x")
        col = 0
        for s in sorted(symptoms):
            tag = tk.Label(row_frame, text=s.replace("_", " "),
                           font=FONT_SMALL, bg=ACCENT, fg="white",
                           padx=8, pady=2)
            tag.grid(row=col // 3, column=col % 3, padx=2, pady=2, sticky="w")
            col += 1

        hr_val = self.hr_entry.get().strip()
        bp_val = self.bp_entry.get().strip()
        vitals_status = "NOT PROVIDED"
        if hr_val and bp_val:
            try:
                vitals_status = check_vitals(int(hr_val), int(bp_val))
            except ValueError:
                vitals_status = "INVALID INPUT"

        disease, confidence = predict_disease(symptoms, self.model, self.mlb)
        severity_score = calculate_severity(symptoms, self.severity_df)
        risk_level = get_risk(severity_score)
        health_cat = get_health_type(disease)
        description = get_description(disease, self.desc_df)
        precautions = get_precautions(disease, self.precaution_df)
        advice = decision_engine(disease, risk_level, vitals_status)

        self._render_report(disease, confidence, health_cat, risk_level,
                            vitals_status, severity_score, description,
                            precautions, advice)

    def _on_clear(self):
        self.symptom_text.delete("1.0", "end")
        self.hr_entry.delete(0, "end")
        self.bp_entry.delete(0, "end")
        for w in self.tag_frame.winfo_children():
            w.destroy()
        self._no_sym_label = tk.Label(self.tag_frame,
                                       text="Symptoms will appear here after analysis",
                                       font=FONT_SMALL, bg=PANEL_BG, fg=TEXT_DIM)
        self._no_sym_label.pack(anchor="w")
        for w in self.report_area.winfo_children():
            w.destroy()
        self._placeholder = tk.Label(
            self.report_area,
            text="Your health report will appear here.\n\n"
                 "Describe your symptoms on the left\nand click  🔍 Analyse.",
            font=FONT_BODY, bg=PANEL_BG, fg=TEXT_DIM, justify="center")
        self._placeholder.pack(expand=True)

    def _render_report(self, disease, confidence, category, risk,
                        vitals, severity_score, description,
                        precautions, advice):
        for w in self.report_area.winfo_children():
            w.destroy()

        canvas = tk.Canvas(self.report_area, bg=PANEL_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.report_area, orient="vertical",
                                   command=canvas.yview)
        inner = tk.Frame(canvas, bg=PANEL_BG)

        inner.bind("<Configure>",
                    lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        stats_frame = tk.Frame(inner, bg=PANEL_BG)
        stats_frame.pack(fill="x", pady=(0, 10))

        risk_col = SUCCESS if risk == "MILD" else (WARNING if risk == "MODERATE" else DANGER)
        conf_col = SUCCESS if confidence >= 70 else (WARNING if confidence >= 40 else DANGER)
        vit_col  = SUCCESS if vitals == "NORMAL" else (
                    WARNING if vitals in ("MODERATE", "NOT PROVIDED") else DANGER)

        self._stat_card(stats_frame, "Predicted Disease", disease, ACCENT, 0)
        self._stat_card(stats_frame, "Confidence", f"{confidence}%", conf_col, 1)
        self._stat_card(stats_frame, "Risk Level", risk, risk_col, 2)
        self._stat_card(stats_frame, "Vitals", vitals, vit_col, 3)

        stats_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="c")

        bar_frame = tk.Frame(inner, bg=CARD_BG, padx=14, pady=10,
                              highlightbackground=BORDER, highlightthickness=1)
        bar_frame.pack(fill="x", pady=(0, 10))
        tk.Label(bar_frame, text="Confidence", font=FONT_SMALL,
                 bg=CARD_BG, fg=TEXT_DIM).pack(anchor="w")
        bar_bg = tk.Canvas(bar_frame, height=12, bg=BG, highlightthickness=0)
        bar_bg.pack(fill="x", pady=(4, 0))
        bar_bg.update_idletasks()
        w = bar_bg.winfo_width() or 400
        fill_w = max(int(w * confidence / 100), 1)
        bar_bg.create_rectangle(0, 0, fill_w, 12, fill=conf_col, outline="")

        if confidence < 50:
            tk.Label(bar_frame,
                     text="⚠️  Low confidence — provide more symptoms for a better match.",
                     font=FONT_SMALL, bg=CARD_BG, fg=WARNING).pack(anchor="w", pady=(4, 0))

        meta = tk.Frame(inner, bg=PANEL_BG)
        meta.pack(fill="x", pady=(0, 10))
        self._info_row(meta, "Health Category", category)
        self._info_row(meta, "Severity Score", str(severity_score))

        desc_frame = tk.Frame(inner, bg=CARD_BG, padx=14, pady=10,
                               highlightbackground=BORDER, highlightthickness=1)
        desc_frame.pack(fill="x", pady=(0, 10))
        tk.Label(desc_frame, text="🧾  Description", font=FONT_HEAD,
                 bg=CARD_BG, fg=TEXT).pack(anchor="w", pady=(0, 4))
        tk.Label(desc_frame, text=description, font=FONT_BODY,
                 bg=CARD_BG, fg=TEXT, wraplength=500,
                 justify="left").pack(anchor="w")

        if precautions:
            prec_frame = tk.Frame(inner, bg=CARD_BG, padx=14, pady=10,
                                   highlightbackground=BORDER, highlightthickness=1)
            prec_frame.pack(fill="x", pady=(0, 10))
            tk.Label(prec_frame, text="💊  Recommended Precautions",
                     font=FONT_HEAD, bg=CARD_BG, fg=TEXT).pack(anchor="w", pady=(0, 6))
            for i, p in enumerate(precautions, 1):
                tk.Label(prec_frame, text=f"  {i}.  {p.strip().capitalize()}",
                         font=FONT_BODY, bg=CARD_BG, fg=TEXT,
                         anchor="w").pack(anchor="w", pady=1)

        adv_col = DANGER if "immediately" in advice else (
                  WARNING if "medication" in advice else SUCCESS)
        adv_frame = tk.Frame(inner, bg=adv_col, padx=14, pady=12)
        adv_frame.pack(fill="x", pady=(0, 10))
        tk.Label(adv_frame, text="Final Recommendation", font=FONT_SMALL,
                 bg=adv_col, fg="white").pack(anchor="w")
        tk.Label(adv_frame, text=advice, font=FONT_BIG,
                 bg=adv_col, fg="white", wraplength=500,
                 justify="left").pack(anchor="w", pady=(2, 0))

    def _stat_card(self, parent, label, value, color, col):
        f = tk.Frame(parent, bg=CARD_BG, padx=10, pady=10,
                      highlightbackground=BORDER, highlightthickness=1)
        f.grid(row=0, column=col, padx=3, sticky="nsew")
        tk.Label(f, text=label, font=FONT_SMALL, bg=CARD_BG,
                 fg=TEXT_DIM).pack(anchor="w")
        tk.Label(f, text=value, font=FONT_BIG, bg=CARD_BG,
                 fg=color, wraplength=160, justify="left").pack(anchor="w", pady=(2, 0))

    def _info_row(self, parent, label, value):
        f = tk.Frame(parent, bg=CARD_BG, padx=14, pady=6,
                      highlightbackground=BORDER, highlightthickness=1)
        f.pack(fill="x", pady=(0, 4))
        tk.Label(f, text=label, font=FONT_SMALL, bg=CARD_BG,
                 fg=TEXT_DIM).pack(side="left")
        tk.Label(f, text=value, font=FONT_HEAD, bg=CARD_BG,
                 fg=TEXT).pack(side="right")

if __name__ == "__main__":
    app = HealthApp()
    app.mainloop()