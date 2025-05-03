import os
import time
import pdfplumber
import docx
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("Talent Pool").worksheet("Data")

# Make sure sheet has headers
headers = ["Name", "Education", "Experience (Years)", "Companies", "Skills"]
if not sheet.get_all_values():
    sheet.append_row(headers)

def extract_text_from_pdf(filepath):
    with pdfplumber.open(filepath) as pdf:
        return "\n".join(page.extract_text() or '' for page in pdf.pages)

def extract_text_from_docx(filepath):
    doc = docx.Document(filepath)
    return "\n".join([para.text for para in doc.paragraphs])

def parse_resume(text):
    # Placeholder logic – customize this later
    name = text.split('\n')[0]
    education = "Bachelor's" if "bachelor" in text.lower() else "N/A"
    experience_years = text.lower().count("year")  # crude count
    companies = [line for line in text.split('\n') if any(word in line.lower() for word in ["inc", "ltd", "corp", "solutions"])]
    skills = [word for word in ["python", "excel", "sql", "communication", "leadership"] if word in text.lower()]
    return [name, education, str(experience_years), ", ".join(companies[:3]), ", ".join(skills)]

class ResumeHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return

        filepath = event.src_path
        filename = os.path.basename(filepath)
        print(f"📄 New file detected: {filename}")

        try:
            text = ""
            if filepath.endswith(".pdf"):
                text = extract_text_from_pdf(filepath)
            elif filepath.endswith(".docx"):
                text = extract_text_from_docx(filepath)

            if text:
                data = parse_resume(text)
                sheet.append_row(data)
                print(f"✅ Resume processed and added to sheet: {filename}")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

if __name__ == "__main__":
    folder_to_watch = "HR_Resume"
    print(f"👀 Watching folder: {folder_to_watch}")
    event_handler = ResumeHandler()
    observer = Observer()
    observer.schedule(event_handler, folder_to_watch, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
