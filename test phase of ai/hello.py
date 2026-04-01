import tkinter as tk
from tkinter import font, ttk, messagebox
import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.ensemble import RandomForestClassifier
import sys
import os

# ==============================
# LOAD DATASETS
# ==============================

df = pd.read_csv("archive (1)/dataset.csv")
severity_df = pd.read_csv("archive (1)/Symptom-severity.csv")
desc_df = pd.read_csv("archive (1)/symptom_Description.csv")
precaution_df = pd.read_csv("archive (1)/symptom_precaution.csv")

# ==============================
# PREPROCESS DATA
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

formatted_symptoms = sorted(list([vs.replace("_", " ").title() for vs in valid_symptoms]))
symptom_mapping = {vs.replace("_", " ").title(): vs for vs in valid_symptoms}

# ==============================
# SEVERITY DICT
# ==============================

severity_dict = {}
for i in range(len(severity_df)):
    symptom = str(severity_df.iloc[i]['Symptom']).strip().lower()
    severity_dict[symptom] = severity_df.iloc[i]['weight']

# ==============================
# FUNCTIONS
# ==============================

def predict_disease(symptoms):
    if not symptoms:
        return "Unknown", 0.0
    input_vector = mlb.transform([symptoms])
    probs = model.predict_proba(input_vector)[0]
    idx = probs.argmax()
    return model.classes_[idx], round(probs[idx] * 100, 2)

def calculate_severity(symptoms):
    score = 0
    for s in symptoms:
        if s in severity_dict:
            score += severity_dict[s]
    return score

def get_risk_level(score):
    if score >= 15:
        return "CRITICAL"
    elif score >= 7:
        return "MODERATE"
    else:
        return "MILD"

def get_description(disease):
    row = desc_df[desc_df['Disease'] == disease]
    return row.values[0][1] if not row.empty else "No description available."

def get_precautions(disease):
    row = precaution_df[precaution_df['Disease'] == disease]
    return list(row.values[0][1:]) if not row.empty else ["Consult a medical professional."]


# ==============================
# UI SETUP
# ==============================

BG_COLOR = "#f8fafc"
PRIMARY_COLOR = "#0ea5e9"
PRIMARY_HOVER = "#0284c7"
TEXT_COLOR = "#334155"
SUBTEXT_COLOR = "#64748b"
DANGER_COLOR = "#ef4444"
WARN_COLOR = "#f59e0b"
SAFE_COLOR = "#10b981"

def show_main_ui():
    root = tk.Tk()
    root.title("MedAI - Symptom Checker")
    
    window_width = 800
    window_height = 700 
    
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    center_x = int(screen_width/2 - window_width / 2)
    center_y = int(screen_height/2 - window_height / 2)
    
    root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
    root.configure(bg=BG_COLOR)
    root.resizable(False, False)
    
    title_font = font.Font(family="Helvetica", size=24, weight="bold")
    section_font = font.Font(family="Helvetica", size=14, weight="bold")
    norm_font = font.Font(family="Helvetica", size=12)
    
    # Header
    header_frame = tk.Frame(root, bg=PRIMARY_COLOR, pady=15)
    header_frame.pack(fill="x")
    tk.Label(header_frame, text="MEDAI SYMPTOM CHECKER", font=title_font, fg="white", bg=PRIMARY_COLOR).pack()
    
    selected_symptoms = []
    
    # Input Area
    input_frame = tk.Frame(root, bg=BG_COLOR, pady=20)
    input_frame.pack()
    
    tk.Label(input_frame, text="Select a Symptom:", font=section_font, bg=BG_COLOR, fg=TEXT_COLOR).pack(side="left", padx=10)
    
    symptom_cb = ttk.Combobox(input_frame, values=formatted_symptoms, state="readonly", font=norm_font, width=30)
    symptom_cb.pack(side="left", padx=10)
    
    def add_symptom():
        display_symp = symptom_cb.get()
        if display_symp:
            raw_symp = symptom_mapping[display_symp]
            if raw_symp not in selected_symptoms:
                selected_symptoms.append(raw_symp)
                listbox.insert(tk.END, display_symp)
            symptom_cb.set('')
            
    add_btn = tk.Button(input_frame, text="Add", font=norm_font, bg=PRIMARY_COLOR, fg="white", relief="flat", padx=10, command=add_symptom)
    add_btn.pack(side="left")
    
    # Listbox of symptoms
    list_frame = tk.Frame(root, bg=BG_COLOR)
    list_frame.pack(pady=10)
    
    tk.Label(list_frame, text="Your Symptoms:", font=section_font, bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w")
    listbox = tk.Listbox(list_frame, font=norm_font, width=50, height=5, relief="solid", bd=1)
    listbox.pack()
    
    def remove_symptom():
        sel = listbox.curselection()
        if sel:
            idx = sel[0]
            listbox.delete(idx)
            selected_symptoms.pop(idx)
            
    tk.Button(list_frame, text="Remove Selected", font=norm_font, fg=DANGER_COLOR, bg=BG_COLOR, relief="flat", command=remove_symptom).pack(anchor="e", pady=5)
    
    # Result Frame
    res_frame = tk.Frame(root, bg=BG_COLOR, pady=10)
    res_frame.pack(fill="both", expand=True, padx=40)
    
    def clear_results():
        for widget in res_frame.winfo_children():
            widget.destroy()
            
    def predict():
        if not selected_symptoms:
            messagebox.showwarning("Empty", "Please add at least one symptom.")
            return
            
        clear_results()
        
        disease, confidence = predict_disease(selected_symptoms)
        score = calculate_severity(selected_symptoms)
        risk = get_risk_level(score)
        desc = get_description(disease)
        precs = get_precautions(disease)
        
        lbl_font = font.Font(family="Helvetica", size=18, weight="bold")
        bold_norm = font.Font(family="Helvetica", size=12, weight="bold")
        
        tk.Label(res_frame, text="AI PREDICTION", font=section_font, bg=BG_COLOR, fg=SUBTEXT_COLOR).pack(anchor="w")
        tk.Label(res_frame, text=disease, font=lbl_font, bg=BG_COLOR, fg=PRIMARY_COLOR).pack(anchor="w", pady=5)
        
        # Badges
        badge_f = tk.Frame(res_frame, bg=BG_COLOR)
        badge_f.pack(anchor="w", pady=5)
        tk.Label(badge_f, text=f" Confidence: {confidence}% ", font=bold_norm, bg="#334155", fg="white", padx=10, pady=5).pack(side="left", padx=(0,10))
        risk_color = DANGER_COLOR if risk == "CRITICAL" else (WARN_COLOR if risk == "MODERATE" else SAFE_COLOR)
        tk.Label(badge_f, text=f" Risk Level: {risk} ", font=bold_norm, bg=risk_color, fg="white", padx=10, pady=5).pack(side="left")
        
        # Details
        tk.Label(res_frame, text="Description:", font=bold_norm, bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(15,5))
        tk.Label(res_frame, text=desc, font=norm_font, bg=BG_COLOR, fg=SUBTEXT_COLOR, wraplength=700, justify="left").pack(anchor="w")
        
        tk.Label(res_frame, text="Recommended Actions:", font=bold_norm, bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w", pady=(15,5))
        for p in precs:
            if str(p).strip() and str(p) != 'nan':
                 tk.Label(res_frame, text=f"• {str(p).capitalize()}", font=norm_font, bg=BG_COLOR, fg=TEXT_COLOR).pack(anchor="w")
    
    submit_btn = tk.Button(root, text="Predict Disease", font=font.Font(family="Helvetica", size=14, weight="bold"), 
                           bg=PRIMARY_COLOR, fg="white", relief="flat", width=20, pady=10, cursor="hand2", command=predict)
    submit_btn.pack(pady=10)
    
    def on_enter(e): submit_btn['background'] = PRIMARY_HOVER
    def on_leave(e): submit_btn['background'] = PRIMARY_COLOR
    submit_btn.bind("<Enter>", on_enter)
    submit_btn.bind("<Leave>", on_leave)

    root.mainloop()

if __name__ == "__main__":
    show_main_ui()
