import pytesseract
from PIL import Image
import os

# ==============================
# SET TESSERACT PATH (IMPORTANT)
# ==============================
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# ==============================
# FUNCTION: EXTRACT TEXT
# ==============================

def extract_text(image_path):
    """Refactored as a clean module function for import."""
    try:
        if not os.path.exists(image_path):
            return "Error: Image file not found."
            
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        return text.strip() if text else "No text detected in image."
    except Exception as e:
        return f"Error analyzing report: {str(e)}"

# ==============================
# MAIN (Standalone test)
# ==============================

if __name__ == "__main__":
    print("\n===== OCR REPORT SCANNER =====")
    image_path = "report.png"
    text = extract_text(image_path)
    print("\n===== EXTRACTED TEXT =====\n")
    print(text)