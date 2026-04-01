"""
MedAi Health Platform - Unified Codebase
Consolidated Patient Intake, Doctor Portal, and OCR Integration.
"""

import tkinter as tk
from tkinter import messagebox, ttk, font, filedialog
import json
import os
import subprocess
import sys
import random
from datetime import datetime
import step1_ocr  # Custom OCR module for reports

# ── COLOUR PALETTE (Premium Dark Theme) ──────────────────────────────
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

# ── DATA STORAGE ─────────────────────────────────────────────────────
DATA_FILE = "patient_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                # Ensure structure exists
                if "patients" not in data: data = {"patients": data, "doctors": {}}
                if "doctors" not in data: data["doctors"] = {}
                # Initialize the mandatory doc if not exists
                if "123ABC" not in data["doctors"]:
                    data["doctors"]["123ABC"] = {"pass": "1234", "requests": [], "linked_patients": []}
                return data
        except:
            return {"patients": {}, "doctors": {"123ABC": {"pass": "1234", "requests": [], "linked_patients": []}}}
    return {"patients": {}, "doctors": {"123ABC": {"pass": "1234", "requests": [], "linked_patients": []}}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ── DISEASE DATABASE & DOCTOR QUESTIONS ──────────────────────────────
DISEASE_QUESTIONS = {
    "Cholera": [
        "How many days have you had frequent watery diarrhea?",
        "How many times are you passing stool per day?",
        "Since when did the vomiting start?",
        "How long have you felt dehydrated (dry mouth/low urine)?",
        "Are symptoms like muscle cramps getting worse or better?"
    ],
    "Malaria": [
        "Since when do you have a high fever with chills?",
        "How often does the sweating occur after fever episodes?",
        "How bad is your headache or body pain (Scale 1–10)?",
        "Have you been in a mosquito-prone area recently?",
        "Are you taking any fever medication, and has it helped?"
    ],
    "Chickenpox": [
        "When did the itchy red rashes or blisters first appear?",
        "How fast is the rash spreading (Improving/Worsening)?",
        "How long have you had fever since the rash started?",
        "Have you applied any medication or cream to the blisters?",
        "Have you had chickenpox before in your life?"
    ],
    "Asthma": [
        "How long have you been experiencing shortness of breath?",
        "How often do the wheezing episodes occur per week?",
        "How severe is the chest tightness during activity?",
        "Do the symptoms worsen specifically at night or during exercise?",
        "How long have you been using an inhaler for relief?"
    ],
    "Dengue": [
        "Since when did the sudden high fever start?",
        "How severe is the joint/muscle pain (Scale 1–10)?",
        "How long have you had pain behind the eyes?",
        "When did any skin rashes or bleeding (gums/nose) appear?",
        "Have symptoms worsened over the last 48 hours?"
    ],
    "Typhoid": [
        "How many days have you had a prolonged fever?",
        "How long after eating do you feel abdominal pain?",
        "Are your symptoms (constipation/diarrhea) improving or worsening?",
        "Since when did you lose your appetite or start feeling weak?",
        "Have you taken any antibiotics for this current episode?"
    ],
    "Common Cold / Flu": [
        "When did the runny/blocked nose and sneezing begin?",
        "How frequent is your sneezing throughout the day?",
        "How long have you had a sore throat or cough?",
        "Is the fever mild or has it increased in intensity?",
        "What treatments have you tried (rest/medicine) and did they help?"
    ],
    "COVID-19": [
        "When did the fever and dry cough symptoms begin?",
        "How long have you had a loss of taste or smell?",
        "How often are you experiencing difficulty breathing?",
        "Have you been in contact with an infected person recently?",
        "Did you take a test, and if so, how many days ago?"
    ],
    "Diabetes": [
        "How long have you been experiencing excessive thirst/urination?",
        "How often do you monitor your blood sugar levels?",
        "Since when did the unexplained weight loss start?",
        "What is your current or most recent glucose level reading?",
        "Are you on insulin or tablets, and are they helping?"
    ],
    "Hypertension": [
        "How long have you been experiencing frequent headaches/dizziness?",
        "How often do you check your blood pressure regularly?",
        "What is your current BP reading (Systolic/Diastolic)?",
        "How severe is your chest pain when it occurs (1–10)?",
        "Are you taking BP medication consistently every day?"
    ]
}

# ── UI COMPONENTS ───────────────────────────────────────────────────

class MedAiApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("MedAi Portal")
        self.geometry("1100x820")
        self.configure(bg=BG)
        
        self.data = load_data()
        self.user_session = {}
        self.temp_user = {}
        self.current_otp = None
        self.poll_after_id = None
        
        self.font_title = font.Font(family="Segoe UI", size=26, weight="bold")
        self.font_head = font.Font(family="Segoe UI", size=14, weight="bold")
        self.font_body = font.Font(family="Segoe UI", size=11)
        self.font_small = font.Font(family="Segoe UI", size=9)
        
        self.container = tk.Frame(self, bg=BG)
        self.container.pack(fill="both", expand=True)
        
        self.show_welcome()

    # ── HELPERS ─────────────────────────────────────────────────────
    
    def clear_container(self):
        if self.poll_after_id:
            self.after_cancel(self.poll_after_id)
            self.poll_after_id = None
            
        for widget in self.container.winfo_children():
            widget.destroy()

    def create_scrollable_container(self, parent):
        container = tk.Frame(parent, bg=BG)
        container.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(container, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=BG)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

        def on_canvas_configure(e):
            canvas.itemconfig(canvas_window, width=e.width)
        canvas.bind("<Configure>", on_canvas_configure)

        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _bind_mw(event): canvas.bind_all("<MouseWheel>", _on_mousewheel)
        def _unbind_mw(event): canvas.unbind_all("<MouseWheel>")
        
        canvas.bind("<Enter>", _bind_mw)
        canvas.bind("<Leave>", _unbind_mw)
        
        return scrollable_frame

    def styled_entry(self, parent, label, show=None):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="x", padx=100, pady=8)
        tk.Label(frame, text=label, font=self.font_head, fg=TEXT, bg=BG).pack(anchor="w", padx=2)
        e = tk.Entry(frame, font=self.font_body, bg=CARD_BG, fg=TEXT, insertbackground=TEXT, 
                     bd=0, highlightbackground=BORDER, highlightthickness=1)
        e.pack(fill="x", pady=5, ipady=10)
        if show: e.config(show=show)
        return e

    def styled_button(self, parent, text, cmd, theme="accent"):
        color = ACCENT if theme == "accent" else PANEL_BG
        hover = ACCENT_HOVER if theme == "accent" else CARD_BG
        btn_frame = tk.Frame(parent, bg=BG)
        btn_frame.pack(pady=20)
        btn = tk.Button(btn_frame, text=text, font=self.font_head, bg=color, fg="white", 
                        activebackground=hover, activeforeground="white", bd=0, 
                        cursor="hand2", command=cmd, pady=12, width=30)
        btn.pack()
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda e: btn.configure(bg=color))
        return btn

    def create_dropdown(self, parent, label, options):
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="x", padx=100, pady=8)
        tk.Label(frame, text=label, font=self.font_head, fg=TEXT, bg=BG).pack(anchor="w", padx=2)
        cb = ttk.Combobox(frame, values=options, state="readonly", font=self.font_body)
        cb.pack(fill="x", pady=5, ipady=5)
        return cb

    # ── AUTH PAGES ───────────────────────────────────────────────────

    def show_welcome(self):
        self.clear_container()
        frame = tk.Frame(self.container, bg=BG)
        frame.place(relx=0.5, rely=0.4, anchor="center")
        
        tk.Label(frame, text="🩺", font=("Segoe UI Emoji", 64), bg=BG, fg=ACCENT).pack()
        tk.Label(frame, text="Welcome to MedAi", font=self.font_title, fg=TEXT, bg=BG).pack(pady=10)
        tk.Label(frame, text="Professional Healthcare Platform", font=self.font_body, fg=TEXT_DIM, bg=BG).pack(pady=(0, 40))
        
        self.styled_button(frame, "Patient Login", self.show_login)
        self.styled_button(frame, "Doctor Portal", self.show_doctor_login, theme="dark")

    def show_login(self):
        self.clear_container()
        tk.Label(self.container, text="Patient Login", font=self.font_title, fg=ACCENT, bg=BG).pack(pady=(40, 5))
        
        email_e = self.styled_entry(self.container, "Email Address")
        pass_e = self.styled_entry(self.container, "Password", show="*")
        
        def do_login():
            email = email_e.get().strip()
            password = pass_e.get().strip()
            patients = self.data.get("patients", {})
            if email in patients and patients[email].get("password") == password:
                self.current_otp = str(random.randint(1000, 9999))
                messagebox.showinfo("OTP Sent", f"Your login OTP is: {self.current_otp}")
                self.show_otp_verify(lambda: self.login_patient(email))
            else:
                messagebox.showerror("Error", "Invalid credentials.")

        self.styled_button(self.container, "Login", do_login)
        tk.Button(self.container, text="Create an account", font=self.font_body, bg=BG, fg=ACCENT, bd=0, command=self.show_signup_1).pack()

    def show_doctor_login(self):
        self.clear_container()
        tk.Label(self.container, text="Doctor Access", font=self.font_title, fg=ACCENT, bg=BG).pack(pady=(40, 5))
        
        doc_id_e = self.styled_entry(self.container, "Doctor ID")
        doc_pass_e = self.styled_entry(self.container, "Password", show="*")
        
        def verify_doc():
            id_ = doc_id_e.get().strip()
            pw = doc_pass_e.get().strip()
            if id_ in self.data["doctors"] and self.data["doctors"][id_]["pass"] == pw:
                self.login_doctor(id_)
            else:
                messagebox.showerror("Error", "Invalid ID or Password.")

        self.styled_button(self.container, "Doctor Login", verify_doc)
        tk.Button(self.container, text="← Back", font=self.font_body, bg=BG, fg=TEXT_DIM, bd=0, command=self.show_welcome).pack()

    def login_patient(self, email):
        self.user_session = self.data["patients"][email]
        self.show_dashboard(email)

    def login_doctor(self, doc_id):
        self.user_session = self.data["doctors"][doc_id]
        self.user_session["id"] = doc_id
        self.show_doctor_dashboard()

    def show_otp_verify(self, success_cmd):
        self.clear_container()
        tk.Label(self.container, text="Verify OTP", font=self.font_title, fg=ACCENT, bg=BG).pack(pady=(40, 5))
        otp_e = self.styled_entry(self.container, "Submit OTP")
        def verify():
            if otp_e.get().strip() == self.current_otp:
                success_cmd()
            else:
                messagebox.showerror("Error", "Wrong OTP.")
        self.styled_button(self.container, "Verify", verify)

    # ── SIGNUP FLOW ─────────────────────────────────────────────────

    def show_signup_1(self):
        self.clear_container()
        tk.Label(self.container, text="Create Account", font=self.font_title, fg=ACCENT, bg=BG).pack(pady=(40, 5))
        email_e = self.styled_entry(self.container, "Email ID")
        pass_e = self.styled_entry(self.container, "Password", show="*")
        
        def get_otp():
            if email_e.get() and pass_e.get():
                self.temp_user = {"email": email_e.get(), "password": pass_e.get()}
                self.current_otp = str(random.randint(1000, 9999))
                messagebox.showinfo("OTP", f"OTP: {self.current_otp}")
            else:
                messagebox.showwarning("Error", "Fill all fields.")

        tk.Button(self.container, text="Get OTP", font=self.font_body, bg=BG, fg=ACCENT, bd=0, command=get_otp).pack()
        otp_e = self.styled_entry(self.container, "Enter OTP")
        
        def next_step():
            if otp_e.get() == self.current_otp: self.show_signup_2()
            else: messagebox.showerror("Error", "Wrong OTP.")

        self.styled_button(self.container, "Next step", next_step)

    def show_signup_2(self):
        self.clear_container()
        tk.Label(self.container, text="Basic Info", font=self.font_title, fg=ACCENT, bg=BG).pack(pady=(40, 5))
        inner = self.create_scrollable_container(self.container)
        
        name_e = self.styled_entry(inner, "Full Name")
        age_e = self.styled_entry(inner, "Age")
        gender_c = self.create_dropdown(inner, "Gender", ["Male", "Female", "Other"])
        dob_e = self.styled_entry(inner, "DOB (DD/MM/YYYY)")
        phone_e = self.styled_entry(inner, "Phone Number")
        addr_e = self.styled_entry(inner, "Address")
        blood_c = self.create_dropdown(inner, "Blood Group", ["Unknown", "A+", "B+", "O+", "AB+", "A-", "B-", "O-", "AB-"])
        
        tk.Label(inner, text="Existing condition?", font=self.font_head, fg=TEXT, bg=BG).pack(pady=20, padx=100, anchor="w")
        has_cond = tk.StringVar(value="No")
        radio_f = tk.Frame(inner, bg=BG)
        radio_f.pack(fill="x", padx=100)
        tk.Radiobutton(radio_f, text="Yes", variable=has_cond, value="Yes", bg=BG, fg=TEXT, selectcolor=PANEL_BG).pack(side="left")
        tk.Radiobutton(radio_f, text="No", variable=has_cond, value="No", bg=BG, fg=TEXT, selectcolor=PANEL_BG).pack(side="left", padx=30)

        def proceed():
            self.temp_user.update({
                "name": name_e.get(), "age": age_e.get(), "gender": gender_c.get(),
                "dob": dob_e.get(), "phone": phone_e.get(), "address": addr_e.get(),
                "blood_group": blood_c.get(), "has_existing": has_cond.get()
            })
            if has_cond.get() == "Yes": self.show_signup_3()
            else: self.show_review()

        self.styled_button(inner, "Continue", proceed)
        tk.Frame(inner, bg=BG, height=50).pack()

    def show_signup_3(self):
        self.clear_container()
        tk.Label(self.container, text="Medical Background", font=self.font_title, fg=ACCENT, bg=BG).pack(pady=(40, 5))
        inner = self.create_scrollable_container(self.container)
        
        mv, me, _ = self.create_bool_detail(inner, "Medications?", "Specify...")
        av, ae, _ = self.create_bool_detail(inner, "Allergies?", "Specify...")
        hv, he, _ = self.create_bool_detail(inner, "Hospitalized recently?", "Why/When...")

        def proceed():
            self.temp_user["med_history"] = {
                "medications": me.get() if mv.get() == "Yes" else "None",
                "allergies": ae.get() if av.get() == "Yes" else "None",
                "hospitalization": he.get() if hv.get() == "Yes" else "None"
            }
            self.show_signup_4()

        self.styled_button(inner, "Disease selection", proceed)

    def create_bool_detail(self, parent, q, placeholder):
        f = tk.Frame(parent, bg=BG)
        f.pack(fill="x", padx=100, pady=10)
        tk.Label(f, text=q, font=self.font_head, fg=TEXT, bg=BG).pack(anchor="w", padx=2)
        var = tk.StringVar(value="No")
        rf = tk.Frame(f, bg=BG); rf.pack(anchor="w")
        tk.Radiobutton(rf, text="Yes", variable=var, value="Yes", bg=BG, fg=TEXT).pack(side="left")
        tk.Radiobutton(rf, text="No", variable=var, value="No", bg=BG, fg=TEXT).pack(side="left", padx=10)
        et = tk.Entry(f, font=self.font_body, bg=CARD_BG, fg=TEXT, bd=0, highlightbackground=BORDER, highlightthickness=1)
        et.insert(0, placeholder); et.pack(fill="x", pady=5, ipady=5)
        return var, et, placeholder

    def show_signup_4(self):
        self.clear_container()
        tk.Label(self.container, text="Disease Selection", font=self.font_title, fg=ACCENT, bg=BG).pack(pady=(40, 5))
        inner = self.create_scrollable_container(self.container)
        var = tk.StringVar(value="Cholera")
        f = tk.Frame(inner, bg=BG); f.pack(pady=10, padx=100, anchor="w")
        for d in DISEASE_QUESTIONS.keys():
            tk.Radiobutton(f, text=d, variable=var, value=d, bg=BG, fg=TEXT, font=self.font_body, selectcolor=PANEL_BG).pack(anchor="w", pady=5)
        def next_q():
            self.temp_user["selected_disease"] = var.get()
            self.show_disease_details(var.get())
        self.styled_button(inner, "Next", next_q)

    def show_disease_details(self, disease):
        self.clear_container()
        tk.Label(self.container, text=f"{disease} Details", font=self.font_title, fg=ACCENT, bg=BG).pack(pady=(40, 5))
        inner = self.create_scrollable_container(self.container)
        qs = DISEASE_QUESTIONS[disease]
        ents = []
        for q in qs: ents.append(self.styled_entry(inner, q))
        def finish():
            self.temp_user["disease_answers"] = {qs[i]: ents[i].get() for i in range(len(qs))}
            self.show_review()
        self.styled_button(inner, "Complete review", finish)

    def show_review(self):
        self.clear_container()
        tk.Label(self.container, text="Review Details", font=self.font_title, fg=ACCENT, bg=BG).pack(pady=(40, 5))
        inner = self.create_scrollable_container(self.container)
        def block(t, d):
            tk.Label(inner, text=t, font=self.font_head, fg=ACCENT, bg=BG).pack(anchor="w", pady=(15,5), padx=100)
            for k,v in d.items():
                if isinstance(v, dict):
                    for sk, sv in v.items(): tk.Label(inner, text=f"• {sk}: {sv}", font=self.font_body, fg=TEXT_DIM, bg=BG).pack(anchor="w", padx=120)
                else: tk.Label(inner, text=f"• {k}: {v}", font=self.font_body, fg=TEXT, bg=BG).pack(anchor="w", padx=110)
        block("Demographics", {k:v for k,v in self.temp_user.items() if not isinstance(v,dict)})
        if "med_history" in self.temp_user: block("History", self.temp_user["med_history"])
        if "disease_answers" in self.temp_user: block("Conditions", self.temp_user["disease_answers"])
        def cnf():
            e = self.temp_user["email"]
            self.data["patients"][e] = self.temp_user
            save_data(self.data); self.login_patient(e)
        self.styled_button(inner, "Confirm & Start", cnf)

    # ── DASHBOARDS ──────────────────────────────────────────────────

    def show_dashboard(self, email):
        self.clear_container()
        nav = tk.Frame(self.container, bg=PANEL_BG, height=70); nav.pack(fill="x")
        tk.Label(nav, text="MedAi Dashboard", font=self.font_head, fg=TEXT, bg=PANEL_BG).pack(side="left", padx=20)
        tk.Button(nav, text=f"👤 {self.user_session.get('name','User')}", bg=ACCENT, fg="white", bd=0, padx=15, command=self.show_profile_sidebar).pack(side="right", padx=20, pady=15)
        body = tk.Frame(self.container, bg=BG); body.pack(fill="both", expand=True, padx=40, pady=40)
        tk.Label(body, text=f"Hello, {self.user_session.get('name','User')}", font=self.font_title, fg=TEXT, bg=BG).pack(anchor="w")
        grid = tk.Frame(body, bg=BG); grid.pack(fill="x", pady=20)
        self.create_card(grid, 0, 0, "Talk to AI", "Predict symptoms with AI.", "Launch Chat", 
                         lambda: subprocess.Popen([sys.executable, "ai_sync.py", self.user_session.get("email", "")]))
        self.create_card(grid, 0, 1, "Medical records", "View Reports uploaded by doctor.", "View History", self.show_records)

    def create_card(self, parent, r, c, title, desc, btxt, cmd):
        f = tk.Frame(parent, bg=CARD_BG, padx=30, pady=30, highlightbackground=BORDER, highlightthickness=1)
        f.grid(row=r, column=c, padx=10, pady=10, sticky="nsew")
        tk.Label(f, text=title, font=self.font_head, fg=TEXT, bg=CARD_BG).pack(anchor="w")
        tk.Label(f, text=desc, font=self.font_body, fg=TEXT_DIM, bg=CARD_BG, wraplength=250).pack(anchor="w", pady=10)
        self.styled_button(f, btxt, cmd).pack(anchor="w")

    def show_records(self):
        # Reload latest data from disk
        self.data = load_data()
        email = self.user_session.get("email")
        if email in self.data["patients"]:
            self.user_session = self.data["patients"][email]
            
        recs = self.user_session.get("records", [])
        if not recs: messagebox.showinfo("Info", "No records found."); return
        win = tk.Toplevel(self); win.geometry("700x800"); win.configure(bg=PANEL_BG)
        win.title("Medical History")
        inner = self.create_scrollable_container(win); inner.configure(bg=PANEL_BG)
        
        # Categorize
        ai_recs = [r for r in recs if r.get("type") == "AI Consultation"]
        doc_recs = [r for r in recs if r.get("type") in ("OCR Report", "Medical Report")]

        def draw_section(title, icon, items):
            tk.Label(inner, text=f"{icon} {title}", font=self.font_title, fg=ACCENT, bg=PANEL_BG).pack(anchor="w", padx=30, pady=(20, 10))
            if not items:
                tk.Label(inner, text="No entries in this section.", font=self.font_body, fg=TEXT_DIM, bg=PANEL_BG).pack(anchor="w", padx=50)
            for r in reversed(items):
                f = tk.Frame(inner, bg=CARD_BG, pady=12, padx=18, highlightbackground=BORDER, highlightthickness=1)
                f.pack(fill="x", padx=30, pady=5)
                tk.Label(f, text=r['date'], font=self.font_small, fg=SUCCESS, bg=CARD_BG).pack(anchor="w")
                tk.Label(f, text=r['content'], font=self.font_body, fg=TEXT, bg=CARD_BG, wraplength=550, justify="left").pack(anchor="w", pady=(5,0))
                if r.get("image_path"):
                    tk.Button(f, text="🔍 AI Analysis", font=self.font_small, bg=ACCENT, fg="white", 
                             command=lambda p=r["image_path"]: subprocess.Popen([sys.executable, "report_ai_ui.py", p])).pack(anchor="e")

        draw_section("AI Consultations", "🔍", ai_recs)
        tk.Frame(inner, bg=BORDER, height=2).pack(fill="x", padx=50, pady=30)
        draw_section("Doctor Reports", "📄", doc_recs)
        
        tk.Button(inner, text="Close", font=self.font_head, bg=PANEL_BG, fg=DANGER, bd=0, command=win.destroy, pady=30).pack()
        tk.Frame(inner, bg=PANEL_BG, height=50).pack()

    def show_profile_sidebar(self):
        side = tk.Toplevel(self); side.geometry("500x800"); side.configure(bg=PANEL_BG)
        inner = self.create_scrollable_container(side); inner.configure(bg=PANEL_BG)
        u = self.user_session
        for l,v in [("Name",u.get("name")),("Blood",u.get("blood_group")),("Phone",u.get("phone"))]:
            tk.Label(inner, text=f"{l}: {v}", font=self.font_body, fg=TEXT, bg=PANEL_BG).pack(anchor="w", padx=30, pady=2)
        tk.Frame(inner, bg=BORDER, height=1).pack(fill="x", padx=30, pady=20)
        tk.Label(inner, text="Link Your Doctor", font=self.font_head, fg=ACCENT, bg=PANEL_BG).pack(anchor="w", padx=30)
        eid = tk.Entry(inner, font=self.font_body, bg=CARD_BG, fg=TEXT, bd=0, highlightthickness=1); eid.pack(fill="x", padx=30, pady=10, ipady=8)
        def lnk():
            d = eid.get().strip()
            if d in self.data["doctors"]:
                m = u["email"]
                if m not in self.data["doctors"][d]["requests"]:
                    self.data["doctors"][d]["requests"].append(m); save_data(self.data)
                    messagebox.showinfo("Sent", "Request sent!"); side.destroy()
            else: messagebox.showerror("Error", "ID not found.")
        tk.Button(inner, text="Send Request", bg=ACCENT, fg="white", bd=0, command=lnk, pady=10).pack(fill="x", padx=30)
        tk.Button(inner, text="Close", font=self.font_small, bg=PANEL_BG, fg=DANGER, bd=0, command=side.destroy, pady=20).pack()

    def show_doctor_dashboard(self):
        self.clear_container()
        doc_id = self.user_session["id"]
        
        # Navbar with notification icon
        nav = tk.Frame(self.container, bg=PANEL_BG, height=70); nav.pack(fill="x")
        tk.Label(nav, text=f"Doctor Desk | {doc_id}", font=self.font_head, fg=TEXT, bg=PANEL_BG).pack(side="left", padx=20)
        
        # Logout
        tk.Button(nav, text="Logout", bg=DANGER, fg="white", bd=0, command=self.show_welcome, padx=15).pack(side="right", padx=20, pady=15)
        
        # Notification Icon + Badge
        self.notif_frame = tk.Frame(nav, bg=PANEL_BG)
        self.notif_frame.pack(side="right", padx=10, pady=15)
        
        self.notif_label = tk.Label(self.notif_frame, text="🔔", font=("Segoe UI Emoji", 16), bg=PANEL_BG, fg=TEXT_DIM)
        self.notif_label.pack(side="left")
        
        self.badge_label = tk.Label(self.notif_frame, text="0", font=self.font_small, bg=DANGER, fg="white", padx=4, pady=1)
        # Badge will be shown/hidden by update_notifications
        
        body = self.create_scrollable_container(self.container)
        self.doctor_body = body # Ref for polling
        
        def update_notifications():
            doc_data = self.data["doctors"].get(doc_id, {})
            reqs = doc_data.get("requests", [])
            count = len(reqs)
            
            if count > 0:
                self.notif_label.config(fg=WARNING)
                self.badge_label.config(text=str(count))
                self.badge_label.place(relx=0.7, rely=0.1)
            else:
                self.notif_label.config(fg=TEXT_DIM)
                self.badge_label.place_forget()

        def poll_requests():
            self.data = load_data()
            update_notifications()
            # If request count changed, refresh the whole body list
            self.poll_after_id = self.after(5000, poll_requests)
            
        update_notifications()
        self.poll_after_id = self.after(5000, poll_requests)

        doc_data = self.data["doctors"][doc_id]
        reqs = doc_data.get("requests", [])
        if reqs:
            rf = tk.Frame(body, bg=CARD_BG, pady=15, padx=20, highlightbackground=WARNING, highlightthickness=1)
            rf.pack(fill="x", padx=40, pady=20)
            tk.Label(rf, text=f"🔔 New Connection Requests", font=self.font_head, fg=WARNING, bg=CARD_BG).pack(anchor="w")
            for r in reqs:
                row = tk.Frame(rf, bg=CARD_BG); row.pack(fill="x", pady=2)
                tk.Label(row, text=r, fg=TEXT, bg=CARD_BG, font=self.font_body).pack(side="left")
                def acc(e=r):
                    self.data["doctors"][doc_id]["requests"].remove(e)
                    self.data["doctors"][doc_id]["linked_patients"].append(e)
                    save_data(self.data); self.show_doctor_dashboard()
                tk.Button(row, text="Accept", bg=SUCCESS, fg="white", font=self.font_small, bd=0, padx=10, command=acc).pack(side="right")
        tk.Label(body, text="Patients", font=self.font_title, fg=TEXT, bg=BG).pack(anchor="w", padx=40, pady=10)
        for p in doc_data.get("linked_patients", []):
            pf = tk.Frame(body, bg=PANEL_BG, pady=15, padx=20, highlightthickness=1); pf.pack(fill="x", padx=40, pady=5)
            tk.Label(pf, text=p, font=self.font_head, fg=TEXT, bg=PANEL_BG).pack(side="left")
            def up(e=p):
                pth = filedialog.askopenfilename()
                if pth:
                    txt = step1_ocr.extract_text(pth)
                    if "records" not in self.data["patients"][e]: self.data["patients"][e]["records"] = []
                    self.data["patients"][e]["records"].append({
                        "date":datetime.now().strftime("%d %b, %H:%M"), 
                        "type":"OCR Report", 
                        "content":txt,
                        "image_path": pth
                    })
                    save_data(self.data); messagebox.showinfo("Done", "Sent!")
            tk.Button(pf, text="Upload Report", bg=ACCENT, fg="white", command=up).pack(side="right")

if __name__ == "__main__":
    app = MedAiApp(); app.mainloop()
