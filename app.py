import streamlit as st
import requests
import os
from fpdf import FPDF
from dotenv import load_dotenv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.mime.text import MIMEText

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

def call_groq(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-70b-8192",
        "messages": [
            {"role": "system", "content": "You are a professional resume assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    res = requests.post(url, json=payload, headers=headers)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    else:
        return f"Error: {res.status_code} - {res.text}"

def generate_pdf(resume_text, name):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for line in resume_text.split("\n"):
        pdf.multi_cell(0, 10, line)

    filename = f"{name}_resume.pdf"
    pdf.output(filename)
    return filename

def send_email(recipient, file_path, name):
    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = recipient
    msg["Subject"] = "Your AI-Generated Resume"

    body = f"Hi {name},\n\nPlease find attached your resume.\n\nBest,\nAI Resume Generator"
    msg.attach(MIMEText(body, "plain"))

    with open(file_path, "rb") as f:
        attach = MIMEApplication(f.read(), _subtype="pdf")
        attach.add_header("Content-Disposition", "attachment", filename=os.path.basename(file_path))
        msg.attach(attach)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

# ---------------- Streamlit UI ----------------
st.set_page_config(page_title="AI Resume Generator", layout="centered")

st.title("🚀 AI Resume Generator")
st.write("Generate a professional resume in seconds using AI!")

with st.form("resume_form"):
    name = st.text_input("Full Name")
    email = st.text_input("Email")
    phone = st.text_input("Phone Number")
    job = st.text_input("Target Job Title")
    education = st.text_area("Education")
    experience = st.text_area("Experience")
    skills = st.text_area("Skills (comma-separated)")
    certs = st.text_area("Certifications")
    projects = st.text_area("Projects")

    submitted = st.form_submit_button("Generate Resume")

if submitted:
    with st.spinner("Generating your resume..."):
        prompt = f"""
Create a professional resume in plain text for the following person:

Name: {name}
Email: {email}
Phone: {phone}
Job Title Target: {job}
Education: {education}
Experience: {experience}
Skills: {skills}
Certifications: {certs}
Projects: {projects}

Structure it with sections: Contact Info, Summary, Experience, Education, Skills, Certifications, Projects.
Use professional language and formatting.
"""
        resume = call_groq(prompt)

        if "Error" not in resume:
            st.success("Resume generated successfully!")

            st.text_area("📝 Resume Preview", resume, height=400)

            pdf_file = generate_pdf(resume, name)

            with open(pdf_file, "rb") as f:
                st.download_button("📥 Download PDF", f, file_name=pdf_file)

            try:
                send_email(email, pdf_file, name)
                st.info(f"Resume emailed to **{email}** 📧")
            except Exception as e:
                st.error(f"Email failed: {e}")
        else:
            st.error("Failed to generate resume. Check API key or try again.")
