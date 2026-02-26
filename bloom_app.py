import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors

# ---------------- APP CONFIG ----------------
st.set_page_config(page_title="Bloom by The Womb", layout="wide", page_icon="🪷")

# Custom CSS for the "Cartoony" Bloom Look
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@400;600&display=swap');
    html, body, [class*="css"] { font-family: 'Fredoka', sans-serif; background-color: #F9FCF9; }
    .stButton>button { background: #A4C3A2; color: white; border-radius: 20px; border: none; width: 100%; }
    .stMetric { background: white; padding: 15px; border-radius: 15px; border: 1px solid #E1EFE1; }
    </style>
    """, unsafe_allow_html=True)

# ---------------- SESSION INIT ----------------
if "user" not in st.session_state:
    st.session_state.user = None
if "role" not in st.session_state:
    st.session_state.role = None
if "vitals" not in st.session_state:
    st.session_state.vitals = pd.DataFrame(columns=["Date", "Weight", "BP_Sys", "BP_Dia", "Sugar"])

# ---------------- LOGIN ----------------
def login():
    st.title("🪷 Bloom by The Womb")
    st.subheader("Clinical Pregnancy Companion")
    
    col1, col2 = st.columns(2)
    with col1:
        role = st.selectbox("I am a...", ["Patient", "Doctor"])
        name = st.text_input("Full Name")
    with col2:
        st.info("Welcome! This app helps you track vitals and connect with your OB-GYN team.")

    if st.button("Start My Journey"):
        if name:
            st.session_state.user = name
            st.session_state.role = role
            st.rerun()

if st.session_state.user is None:
    login()
    st.stop()

# ---------------- HELPER ENGINES ----------------
def get_baby_size(week):
    sizes = {
        (1, 8): "Raspberry 🍓", (9, 12): "Lime 🍋", (13, 16): "Avocado 🥑",
        (17, 20): "Banana 🍌", (21, 24): "Corn 🌽", (25, 28): "Eggplant 🍆",
        (29, 32): "Coconut 🥥", (33, 36): "Pineapple 🍍", (37, 40): "Watermelon 🍉"
    }
    for r, size in sizes.items():
        if r[0] <= week <= r[1]: return size
    return "Growing beautifully! ✨"

def generate_pdf(df, user_name):
    filename = f"Antenatal_Record_{user_name}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"Bloom Antenatal Record: {user_name}", styles["Title"]), Spacer(1, 12)]
    
    # Table Styling
    data = [df.columns.tolist()] + df.values.tolist()
    t = Table(data)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.whitesmoke),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkgreen),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ]))
    elements.append(t)
    doc.build(elements)
    return filename

# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown(f"### 🪷 Welcome, {st.session_state.user}")
    st.caption(f"Access Level: {st.session_state.role}")
    
    st.divider()
    # Clinical Week Input
    lmp = st.date_input("Last Menstrual Period (LMP)", datetime.now() - timedelta(weeks=16))
    today = datetime.now().date()
    diff_days = (today - lmp).days
    current_week = max(1, min(40, diff_days // 7))
    
    st.metric("Current Week", f"Week {current_week}")
    if st.button("Logout"):
        st.session_state.user = None
        st.rerun()

# ---------------- MAIN TABS (Role-Based) ----------------
# Only show Doctor Panel to Doctors
if st.session_state.role == "Doctor":
    tabs = st.tabs(["🏠 Patient Dashboard", "🩺 Health Logs", "👩‍⚕️ Clinical Admin"])
else:
    tabs = st.tabs(["🏠 My Dashboard", "🩺 My Health Logs", "🤝 The Village"])

# ================= DASHBOARD =================
with tabs[0]:
    st.header(f"The Lotus Nest: Week {current_week}")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown(f"<h1 style='font-size: 100px; text-align: center;'>🪷</h1>", unsafe_allow_html=True)
        st.success(f"Baby is a **{get_baby_size(current_week)}**")
        st.progress(current_week / 40)
    
    with c2:
        st.subheader("Daily Checklist")
        st.checkbox("Prenatal Vitamins", value=True)
        st.checkbox("Hydration Goal (2.5L)")
        st.checkbox("Talk to the Bump")
        
        st.divider()
        st.info("💡 **Dr.'s Tip:** You might start feeling 'flutters' this week! These are early movements.")

# ================= MEDICAL LOG =================
with tabs[1]:
    st.header("Vitals Monitoring")
    
    with st.expander("➕ Add Daily Reading", expanded=True):
        f1, f2, f3 = st.columns(3)
        wt = f1.number_input("Weight (kg)", 40.0, 150.0, 65.0)
        bp_raw = f2.text_input("Blood Pressure (Sys/Dia)", "120/80")
        sug = f3.number_input("Sugar (mg/dL)", 50, 300, 95)
        
        if st.button("Save to Record"):
            try:
                sys, dia = map(int, bp_raw.replace(" ", "").split("/"))
                new_entry = pd.DataFrame([[datetime.now().strftime("%d %b"), wt, sys, dia, sug]], 
                                        columns=["Date", "Weight", "BP_Sys", "BP_Dia", "Sugar"])
                st.session_state.vitals = pd.concat([st.session_state.vitals, new_entry], ignore_index=True)
                st.toast("Record Saved!")
            except:
                st.error("Please use format 120/80")

    # Risk Analysis Logic
    if not st.session_state.vitals.empty:
        last = st.session_state.vitals.iloc[-1]
        if last["BP_Sys"] >= 140 or last["BP_Dia"] >= 90:
            st.error("🚨 **PIH ALERT:** High Blood Pressure. Please rest and call Dr. [Name].")
            
        if last["Sugar"] >= 140:
            st.warning("⚠️ **GDM ALERT:** Elevated Sugar levels detected.")
            
            
        st.line_chart(st.session_state.vitals.set_index("Date")[["Weight", "Sugar"]])
        
        if st.button("📄 Generate Antenatal PDF"):
            pdf_path = generate_pdf(st.session_state.vitals, st.session_state.user)
            with open(pdf_path, "rb") as f:
                st.download_button("Download Official Record", f, file_name=pdf_path)

# ================= ROLE-SPECIFIC TAB =================
if st.session_state.role == "Doctor":
    with tabs[2]:
        st.header("👩‍⚕️ Clinical Oversight")
        st.metric("Total Patients Active", "1") # Scalable with Database
        st.dataframe(st.session_state.vitals, use_container_width=True)
        
        high_risk = st.session_state.vitals[(st.session_state.vitals.BP_Sys >= 140) | (st.session_state.vitals.Sugar >= 140)]
        if not high_risk.empty:
            st.error("⚠️ The following logs require immediate clinical review!")
            st.table(high_risk)
else:
    with tabs[2]:
        st.header("🤝 The Village")
        st.write("Connect with other mamas in your trimester!")
        st.text_area("Share a tip or ask a question...")
        st.button("Post to Village")
        st.divider()
        st.markdown("**📌 Pinned:** Watch Dr. [Name]'s latest video on YouTube!")
