import sys
import json
import os
import time
from test1_ui import HealthApp

class SyncedHealthApp(HealthApp):
    def __init__(self, user_email=None):
        super().__init__()
        self.user_email = user_email
        if user_email:
            self.title(f"AI Assistant | {user_email}")

    def _render_report(self, disease, confidence, category, risk,
                        vitals, severity_score, description,
                        precautions, advice):
        # 1. Call original UI render logic from test1_ui.py
        super()._render_report(disease, confidence, category, risk,
                                vitals, severity_score, description,
                                precautions, advice)
        
        # 2. Silently save the result to the medical records in patient_data.json
        if self.user_email:
            self._save_to_history(disease, confidence, risk, advice)

    def _save_to_history(self, disease, confidence, risk, advice):
        try:
            DATA_FILE = "patient_data.json"
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
                
                if self.user_email in data["patients"]:
                    new_record = {
                        "date": time.strftime("%d %b, %H:%M"),
                        "type": "AI Consultation",
                        "content": f"Prediction: {disease}\nConfidence: {confidence}%\nRisk: {risk}\n\nRecommendation: {advice}"
                    }
                    
                    if "records" not in data["patients"][self.user_email]:
                        data["patients"][self.user_email]["records"] = []
                    
                    data["patients"][self.user_email]["records"].append(new_record)
                    
                    with open(DATA_FILE, "w") as f:
                        json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Medical History Sync Error: {e}")

if __name__ == "__main__":
    # Receive email argument from main.py
    email_arg = sys.argv[1] if len(sys.argv) > 1 else None
    app = SyncedHealthApp(user_email=email_arg)
    app.mainloop()
