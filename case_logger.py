import streamlit as st
import pandas as pd
import json
from datetime import datetime, date, time as dt_time
import os
import requests
import random

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'pin' not in st.session_state:
    st.session_state.pin = None

def show_login():
    """Show login screen with PIN"""
    st.markdown("# 🔒 Anaesthetic Case Logger")
    st.markdown("### Secure Login")
    
    # Check if PIN is set
    pin_file = 'user_pin.json'
    pin_exists = os.path.exists(pin_file)
    
    if not pin_exists:
        st.info("👋 Welcome! Please set up your 4-digit PIN for secure access.")
        col1, col2 = st.columns(2)
        with col1:
            new_pin = st.text_input("Create 4-digit PIN", type="password", max_chars=4, key="new_pin")
        with col2:
            confirm_pin = st.text_input("Confirm PIN", type="password", max_chars=4, key="confirm_pin")
        
        if st.button("Set PIN", type="primary"):
            if len(new_pin) == 4 and new_pin.isdigit():
                if new_pin == confirm_pin:
                    with open(pin_file, 'w') as f:
                        json.dump({'pin': new_pin}, f)
                    st.success("✅ PIN set successfully! Please log in.")
                    st.rerun()
                else:
                    st.error("PINs do not match!")
            else:
                st.error("PIN must be exactly 4 digits!")
    else:
        st.info("🔐 Enter your PIN to continue")
        entered_pin = st.text_input("Enter PIN", type="password", max_chars=4, key="enter_pin")
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Login", type="primary"):
                with open(pin_file, 'r') as f:
                    stored_data = json.load(f)
                
                if entered_pin == stored_data['pin']:
                    st.session_state.authenticated = True
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Incorrect PIN!")
        with col2:
            if st.button("Reset PIN"):
                if os.path.exists(pin_file):
                    os.remove(pin_file)
                st.info("PIN reset. Please set a new PIN.")
                st.rerun()

def check_smart_reminders():
    """Check if it's reminder time (5pm-5:30pm) and show reminder"""
    now = datetime.now()
    current_time = now.time()
    
    # Check if between 5pm and 5:30pm
    if dt_time(17, 0) <= current_time <= dt_time(17, 30):
        # Check if we've already shown reminder today
        reminder_key = f"reminder_shown_{now.date()}"
        
        if reminder_key not in st.session_state:
            st.session_state[reminder_key] = True
            
            # Count incomplete cases
            incomplete = [c for c in st.session_state.cases if not c.get('completed', False)]
            
            if incomplete:
                st.warning(f"""
                ### ⏰ End of Day Reminder
                You have **{len(incomplete)} incomplete case(s)** to finish!
                
                **Why complete them now?**
                - Details are fresh in your mind
                - Takes just 2-3 minutes per case with AI helper
                - Your portfolio stays up to date
                
                👉 Scroll down to complete them before you leave!
                """)

def generate_mcqs_from_cases():
    """Generate Primary FRCA-style MCQs based on saved cases - IMPROVED VERSION"""
    st.markdown("## 📝 Primary FRCA Practice MCQs")
    st.info("AI-generated MCQs based on YOUR logged cases - perfect for revision!")
    
    if not st.session_state.cases:
        st.warning("No cases logged yet. Log some cases first to generate MCQs!")
        return
    
    # IMPROVED: Get cases with ANY clinical information from ANY field
    clinical_cases = []
    for c in st.session_state.cases:
        # Collect ALL text from the case
        case_text = ' '.join(str(v) for v in [
            c.get('notes', ''),
            c.get('procedure', ''),
            c.get('reflection', ''),
            c.get('learning', ''),
            c.get('operation_type', ''),
            c.get('anaesthetic_type', ''),
            c.get('case_type', ''),
            c.get('urgency', ''),
            c.get('asa_grade', ''),
            c.get('age_category', ''),
            c.get('supervision_level', '')
        ] if v)
        
        # Include if there's ANY meaningful content
        if len(case_text.strip()) > 10:  # At least 10 characters of content
            clinical_cases.append(c)
    
    if not clinical_cases:
        st.warning("No cases with sufficient detail found. Add more details to your cases to generate better MCQs!")
        return
    
    st.success(f"✅ Found {len(clinical_cases)} cases with clinical information!")
    
    num_questions = st.slider("Number of questions to generate", 1, 10, 5)
    
    if st.button("🎲 Generate MCQs", type="primary"):
        with st.spinner("Generating MCQs from your cases..."):
            # Check if API key is available
            if not st.session_state.get('anthropic_api_key'):
                st.error("Please enter your Anthropic API key in the AI Assistant section first!")
                return
            
            # Sample cases for MCQ generation
            sampled_cases = random.sample(clinical_cases, min(num_questions, len(clinical_cases)))
            
            # IMPROVED: Prepare context with ALL available information
            cases_summary = []
            for case in sampled_cases:
                summary_parts = []
                
                # Assessment type
                assessment_type = case.get('assessment_type', 'case')
                if assessment_type != 'case':
                    summary_parts.append(f"Assessment: {ASSESSMENT_TYPES.get(assessment_type, assessment_type)}")
                
                # Core details
                if case.get('procedure'):
                    summary_parts.append(f"Procedure: {case['procedure']}")
                if case.get('operation_type'):
                    summary_parts.append(f"Specialty: {case['operation_type']}")
                if case.get('anaesthetic_type'):
                    summary_parts.append(f"Anaesthetic: {case['anaesthetic_type']}")
                if case.get('urgency'):
                    summary_parts.append(f"Urgency: {case['urgency']}")
                if case.get('age_category'):
                    summary_parts.append(f"Patient: {case['age_category']}")
                if case.get('asa_grade'):
                    summary_parts.append(f"ASA: {case['asa_grade']}")
                if case.get('supervision_level'):
                    summary_parts.append(f"Role: {case['supervision_level']}")
                
                # Clinical content
                if case.get('notes'):
                    summary_parts.append(f"Notes: {case['notes'][:300]}")
                if case.get('reflection'):
                    summary_parts.append(f"Reflection: {case['reflection'][:200]}")
                if case.get('learning'):
                    summary_parts.append(f"Learning: {case['learning'][:200]}")
                
                # CBD/CEX scores
                if case.get('cbd_scores'):
                    scores_text = ', '.join([f"{k}: {v}" for k, v in case['cbd_scores'].items() if v])
                    if scores_text:
                        summary_parts.append(f"CBD scores: {scores_text}")
                if case.get('cex_scores'):
                    scores_text = ', '.join([f"{k}: {v}" for k, v in case['cex_scores'].items() if v])
                    if scores_text:
                        summary_parts.append(f"CEX scores: {scores_text}")
                
                cases_summary.append(' | '.join(summary_parts))
            
            prompt = f"""Based on these anaesthetic cases from my clinical practice, generate {num_questions} Primary FRCA-style MCQ questions (SBA format - one best answer from 5 options).

My Cases:
{chr(10).join([f"{i+1}. {s}" for i, s in enumerate(cases_summary)])}

For each question:
1. Create a realistic clinical scenario based on the cases above
2. Ask a question relevant to Primary FRCA (pharmacology, physiology, physics, clinical anaesthesia)
3. Provide 5 options (A-E) with ONE best answer
4. Include a brief explanation of the correct answer

Format each question as:
QUESTION X:
[Clinical scenario and question]
A) [option]
B) [option]
C) [option]
D) [option]
E) [option]

ANSWER: [Letter]
EXPLANATION: [Brief explanation]

---"""
            
            try:
                response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": st.session_state.anthropic_api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json"
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 4000,
                        "messages": [{"role": "user", "content": prompt}]
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    mcqs_text = result['content'][0]['text']
                    
                    st.success(f"✅ Generated {num_questions} MCQs from your cases!")
                    st.markdown("---")
                    st.markdown(mcqs_text)
                    
                    # Download button
                    st.download_button(
                        "📥 Download MCQs",
                        data=mcqs_text,
                        file_name=f"frca_mcqs_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain"
                    )
                else:
                    st.error(f"Error generating MCQs: {response.status_code}")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# Page config
st.set_page_config(
    page_title="Anaesthetic Case Logger",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stat-number {
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
        margin: 0;
    }
    .case-card {
        background: white;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .case-complete {
        opacity: 0.6;
        border-left-color: #10b981;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    .badge-complete {
        background: #d1fae5;
        color: #065f46;
    }
    .badge-incomplete {
        background: #fef3c7;
        color: #92400e;
    }
    .badge-exported {
        background: #dbeafe;
        color: #1e40af;
    }
    .epa-tag {
        display: inline-block;
        background: #e0e7ff;
        color: #3730a3;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.75rem;
        margin: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Data file path
DATA_FILE = "case_logger_data.json"

# Initialize session state
if 'cases' not in st.session_state:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            st.session_state.cases = json.load(f)
    else:
        st.session_state.cases = []

# Check authentication - show login if not authenticated
if not st.session_state.authenticated:
    show_login()
    st.stop()

# Check for smart reminders (5pm-5:30pm)
check_smart_reminders()

if 'show_form' not in st.session_state:
    st.session_state.show_form = False

if 'editing_id' not in st.session_state:
    st.session_state.editing_id = None

if 'show_ai_helper' not in st.session_state:
    st.session_state.show_ai_helper = False

if 'ai_context' not in st.session_state:
    st.session_state.ai_context = {}

if 'assessment_type' not in st.session_state:
    st.session_state.assessment_type = 'case'

# Constants
URGENCY_TYPES = [
    'Elective',
    'Urgent',
    'Emergency',
    'Immediate/Resus'
]

TIME_OF_DAY = [
    'Morning',
    'Afternoon',
    'Evening',
    'Night'
]

ANAESTHETIC_TYPES = [
    'GA - ETT (LMA/SGA if failed)',
    'GA - LMA/SGA',
    'GA - Face mask',
    'TIVA - ETT',
    'TIVA - LMA/SGA',
    'Spinal',
    'Epidural',
    'CSE',
    'Regional block (single shot)',
    'Regional block (catheter)',
    'Regional + sedation',
    'Regional + GA',
    'Local anaesthetic infiltration',
    'Sedation (conscious)',
    'Sedation (deep)',
    'MAC',
    'Awake fibreoptic intubation',
    'Other'
]

SUPERVISION_LEVELS = [
    'Observed (Level 1)',
    'Supervised - Hands on (Level 2)',
    'Supervised - Distant (Level 3a)',
    'Supervised - Immediately available (Level 3b)',
    'Autonomous (Level 4)'
]

OPERATION_TYPES = [
    'General Surgery',
    'Orthopaedic',
    'Vascular',
    'Urology',
    'Gynaecology',
    'Obstetric',
    'ENT',
    'Maxillofacial',
    'Plastics',
    'Neurosurgery',
    'Cardiac',
    'Thoracic',
    'Paediatric',
    'Other'
]

CASE_TYPES = [
    'Emergency - Trauma',
    'Emergency - Non-trauma',
    'Elective - Major',
    'Elective - Minor/Intermediate',
    'Obstetric',
    'Paediatric',
    'ICU/Critical Care',
    'Pain/Regional'
]

COMMON_PROCEDURES = [
    'General Anaesthesia',
    'RSI',
    'Spinal',
    'Epidural',
    'Combined Spinal-Epidural',
    'Nerve Block - Upper Limb',
    'Nerve Block - Lower Limb',
    'Airway Management',
    'Failed Intubation',
    'Arterial Line',
    'Central Line',
    'Pre-operative Assessment',
    'Post-op Review'
]

# Procedures organized by specialty for filtered dropdown
PROCEDURES_BY_SPECIALTY = {
    'General Surgery': [
        'Appendicectomy (open)',
        'Appendicectomy (laparoscopic)',
        'Laparoscopic cholecystectomy',
        'Open cholecystectomy',
        'Inguinal hernia repair',
        'Umbilical hernia repair',
        'Incisional hernia repair',
        'Laparoscopic hernia repair',
        'Emergency laparotomy',
        'Laparotomy (elective)',
        'Small bowel resection',
        'Right hemicolectomy',
        'Left hemicolectomy',
        'Anterior resection',
        'Hartmann\'s procedure',
        'Abdominoperineal resection',
        'Adhesiolysis',
        'Perforated viscus repair',
        'Gastrectomy',
        'Oesophagectomy',
        'Whipple\'s procedure',
        'Splenectomy',
        'Thyroidectomy',
        'Parathyroidectomy',
        'Mastectomy',
        'Wide local excision (breast)',
        'Axillary clearance',
        'Sentinel node biopsy',
        'Incision and drainage',
        'Abscess drainage',
        'Wound debridement',
    ],
    'Orthopaedics': [
        'Total hip replacement (THR)',
        'Hemiarthroplasty (hip)',
        'Total knee replacement (TKR)',
        'Dynamic hip screw (DHS)',
        'Intramedullary nail (femur)',
        'Intramedullary nail (tibia)',
        'ORIF (open reduction internal fixation)',
        'ORIF ankle',
        'ORIF wrist',
        'ORIF humerus',
        'ORIF femur',
        'ORIF tibia',
        'External fixation',
        'Knee arthroscopy',
        'ACL reconstruction',
        'Meniscectomy',
        'Shoulder arthroscopy',
        'Rotator cuff repair',
        'Carpal tunnel decompression',
        'Trigger finger release',
        'Dupuytren\'s contracture release',
        'Hand surgery',
        'Manipulation under anaesthesia (MUA)',
        'Spinal fusion',
        'Laminectomy',
        'Discectomy',
        'Spinal decompression',
        'Amputation (above knee)',
        'Amputation (below knee)',
    ],
    'Obstetrics': [
        'Caesarean section (Category 1)',
        'Caesarean section (Category 2)',
        'Caesarean section (Category 3)',
        'Caesarean section (Category 4)',
        'Caesarean section (elective)',
        'Manual removal of placenta',
        'Examination under anaesthesia',
        'Perineal repair',
        'Cervical cerclage',
        'Labour epidural',
        'Spinal for caesarean section',
        'Combined spinal-epidural (labour)',
    ],
    'Gynaecology': [
        'Total abdominal hysterectomy',
        'Vaginal hysterectomy',
        'Laparoscopic hysterectomy',
        'Ovarian cystectomy',
        'Salpingectomy',
        'Salpingo-oophorectomy',
        'Myomectomy',
        'ERPC (evacuation retained products)',
        'Hysteroscopy',
        'D&C (dilation and curettage)',
        'Diagnostic laparoscopy',
        'Laparoscopy and dye test',
        'Laparoscopic sterilisation',
        'Endometrial ablation',
        'LLETZ',
        'Colposcopy',
        'Anterior repair',
        'Posterior repair',
        'TVT procedure',
        'TOT procedure',
    ],
    'Urology': [
        'TURP (transurethral resection prostate)',
        'TURBT (transurethral resection bladder tumour)',
        'Cystoscopy',
        'Ureteroscopy',
        'Ureteric stent insertion',
        'Nephrectomy',
        'Partial nephrectomy',
        'Radical prostatectomy',
        'Percutaneous nephrolithotomy (PCNL)',
        'Circumcision',
        'Orchidectomy',
        'Orchidopexy',
        'Hydrocele repair',
        'Vasectomy',
        'Urethral dilatation',
    ],
    'Vascular': [
        'AAA repair (open)',
        'EVAR (endovascular aneurysm repair)',
        'Carotid endarterectomy',
        'Femoral-popliteal bypass',
        'Femoral-distal bypass',
        'AV fistula formation',
        'AV fistula revision',
        'Varicose vein surgery',
        'Embolectomy',
        'Thrombectomy',
        'Fasciotomy',
        'Amputation (vascular)',
    ],
    'ENT': [
        'Tonsillectomy',
        'Adenoidectomy',
        'Adenotonsillectomy',
        'Septoplasty',
        'FESS (functional endoscopic sinus surgery)',
        'Microlaryngoscopy',
        'Panendoscopy',
        'Thyroidectomy',
        'Parathyroidectomy',
        'Neck dissection',
        'Myringotomy and grommets',
        'Mastoidectomy',
        'Stapedectomy',
        'Submandibular gland excision',
        'Parotidectomy',
    ],
    'Maxillofacial': [
        'Dental extraction',
        'Wisdom teeth extraction',
        'Multiple dental extractions',
        'Mandibular fracture ORIF',
        'Maxillary fracture ORIF',
        'Zygoma fracture ORIF',
        'Le Fort fracture repair',
        'TMJ arthroscopy',
    ],
    'Plastics': [
        'Skin graft',
        'Split skin graft',
        'Full thickness graft',
        'Flap surgery',
        'Free flap',
        'Carpal tunnel release',
        'Dupuytren\'s contracture release',
        'Hand fracture ORIF',
        'Tendon repair',
        'Burn debridement',
        'Escharotomy',
        'Breast reconstruction',
        'Cleft lip repair',
        'Cleft palate repair',
    ],
    'Neurosurgery': [
        'Craniotomy',
        'Craniectomy',
        'Burr holes',
        'EVD insertion',
        'VP shunt insertion',
        'VP shunt revision',
        'Spinal decompression',
        'Spinal fusion',
        'Discectomy',
        'Laminectomy',
        'Acoustic neuroma excision',
        'Pituitary surgery',
    ],
    'Cardiothoracic': [
        'CABG (coronary artery bypass)',
        'Valve replacement (AVR)',
        'Valve replacement (MVR)',
        'Valve repair',
        'ASD closure',
        'VSD closure',
        'Lobectomy',
        'Pneumonectomy',
        'VATS (video-assisted thoracoscopic surgery)',
        'Mediastinoscopy',
        'Pleurodesis',
        'Chest drain insertion',
        'Thoracotomy',
    ],
    'Paediatric': [
        'Circumcision',
        'Herniotomy',
        'Orchidopexy',
        'Hypospadias repair',
        'Pyloromyotomy',
        'Intussusception reduction',
        'Appendicectomy (paediatric)',
        'Tonsillectomy (paediatric)',
        'Adenoidectomy (paediatric)',
        'Myringotomy and grommets',
    ],
}

# Create flat list of all procedures for "Other" specialty option
ALL_SURGICAL_PROCEDURES = []
for procedures in PROCEDURES_BY_SPECIALTY.values():
    ALL_SURGICAL_PROCEDURES.extend(procedures)
ALL_SURGICAL_PROCEDURES = sorted(list(set(ALL_SURGICAL_PROCEDURES)))  # Remove duplicates and sort

# Specialty list
SPECIALTIES = sorted(list(PROCEDURES_BY_SPECIALTY.keys()))

# EPA suggestions for different assessment types
EPA_SUGGESTIONS = {
    'cbd': {
        'pre-operative assessment': ['EPA1 - Initial Assessment & Management', 'EPA2 - Pre-operative Assessment'],
        'airway management': ['EPA1 - Initial Assessment & Management', 'EPA3 - Safe Conduct of Anaesthesia'],
        'difficult airway': ['EPA1 - Initial Assessment & Management', 'EPA3 - Safe Conduct of Anaesthesia', 'EPA6 - Resuscitation & Transfer'],
        'failed intubation': ['EPA1 - Initial Assessment & Management', 'EPA6 - Resuscitation & Transfer'],
        'emergency case': ['EPA1 - Initial Assessment & Management', 'EPA3 - Safe Conduct of Anaesthesia'],
        'post-operative care': ['EPA4 - Peri-operative Care', 'EPA5 - Managing Acute Pain'],
        'pain management': ['EPA5 - Managing Acute Pain'],
        'regional': ['EPA3 - Safe Conduct of Anaesthesia', 'EPA5 - Managing Acute Pain'],
        'resuscitation': ['EPA6 - Resuscitation & Transfer'],
        'transfer': ['EPA6 - Resuscitation & Transfer'],
        'communication': ['EPA7 - General & Communication Skills'],
        'default': ['EPA1 - Initial Assessment & Management', 'EPA7 - General & Communication Skills']
    },
    'cex': {
        'pre-operative': ['EPA1 - Initial Assessment & Management', 'EPA2 - Pre-operative Assessment'],
        'induction': ['EPA3 - Safe Conduct of Anaesthesia'],
        'maintenance': ['EPA3 - Safe Conduct of Anaesthesia'],
        'emergence': ['EPA3 - Safe Conduct of Anaesthesia', 'EPA4 - Peri-operative Care'],
        'regional': ['EPA3 - Safe Conduct of Anaesthesia', 'EPA5 - Managing Acute Pain'],
        'pain': ['EPA5 - Managing Acute Pain'],
        'default': ['EPA3 - Safe Conduct of Anaesthesia']
    },
    'dops': {
        'arterial line': ['EPA3 - Safe Conduct of Anaesthesia'],
        'central line': ['EPA3 - Safe Conduct of Anaesthesia'],
        'spinal': ['EPA3 - Safe Conduct of Anaesthesia'],
        'epidural': ['EPA3 - Safe Conduct of Anaesthesia'],
        'nerve block': ['EPA3 - Safe Conduct of Anaesthesia', 'EPA5 - Managing Acute Pain'],
        'intubation': ['EPA3 - Safe Conduct of Anaesthesia'],
        'airway': ['EPA3 - Safe Conduct of Anaesthesia'],
        'default': ['EPA3 - Safe Conduct of Anaesthesia']
    },
    'acat': {
        'emergency': ['EPA1 - Initial Assessment & Management', 'EPA6 - Resuscitation & Transfer'],
        'resuscitation': ['EPA6 - Resuscitation & Transfer'],
        'trauma': ['EPA1 - Initial Assessment & Management', 'EPA6 - Resuscitation & Transfer'],
        'default': ['EPA1 - Initial Assessment & Management']
    }
}

SURGICAL_PROCEDURES = [
    # General Surgery
    'Laparoscopic Cholecystectomy',
    'Open Cholecystectomy',
    'Laparoscopic Appendicectomy',
    'Open Appendicectomy',
    'Inguinal Hernia Repair',
    'Umbilical Hernia Repair',
    'Incisional Hernia Repair',
    'Laparoscopic Inguinal Hernia Repair',
    'Emergency Laparotomy',
    'Laparotomy',
    'Hartmann\'s Procedure',
    'Right Hemicolectomy',
    'Left Hemicolectomy',
    'Anterior Resection',
    'Abdominoperineal Resection',
    'Small Bowel Resection',
    'Adhesiolysis',
    'Gastrectomy',
    'Oesophagectomy',
    'Whipple\'s Procedure',
    'Splenectomy',
    'Thyroidectomy',
    'Parathyroidectomy',
    'Mastectomy',
    'Wide Local Excision Breast',
    'Varicose Vein Surgery',
    
    # Orthopaedics
    'Dynamic Hip Screw (DHS)',
    'Total Hip Replacement (THR)',
    'Hemiarthroplasty Hip',
    'Total Knee Replacement (TKR)',
    'Knee Arthroscopy',
    'ACL Reconstruction',
    'Shoulder Arthroscopy',
    'Rotator Cuff Repair',
    'Carpal Tunnel Decompression',
    'Trigger Finger Release',
    'Manipulation Under Anaesthesia (MUA)',
    'ORIF Ankle',
    'ORIF Wrist',
    'ORIF Humerus',
    'ORIF Femur',
    'Intramedullary Nail Femur',
    'Intramedullary Nail Tibia',
    'Spinal Fusion',
    'Laminectomy',
    'Discectomy',
    
    # Urology
    'TURP (Transurethral Resection Prostate)',
    'TURBT (Transurethral Resection Bladder Tumour)',
    'Cystoscopy',
    'Ureteroscopy',
    'Nephrectomy',
    'Partial Nephrectomy',
    'Radical Prostatectomy',
    'Circumcision',
    'Orchidectomy',
    'Orchidopexy',
    'Vasectomy',
    'Urethral Dilatation',
    
    # Gynaecology
    'Caesarean Section',
    'Laparoscopic Sterilisation',
    'Laparoscopy + Dye Test',
    'Hysterectomy (Abdominal)',
    'Hysterectomy (Vaginal)',
    'Hysterectomy (Laparoscopic)',
    'Ovarian Cystectomy',
    'Salpingectomy',
    'Salpingo-oophorectomy',
    'Myomectomy',
    'Endometrial Ablation',
    'Hysteroscopy',
    'D&C (Dilation & Curettage)',
    'ERPC (Evacuation Retained Products)',
    'LLETZ',
    'Colposcopy',
    'Anterior/Posterior Repair',
    'TVT/TOT Procedure',
    
    # Obstetrics
    'Caesarean Section (Elective)',
    'Caesarean Section (Emergency)',
    'Manual Removal of Placenta',
    'Examination Under Anaesthesia',
    'Perineal Repair',
    'Labour Epidural',
    'Spinal for C-Section',
    
    # Vascular
    'AAA Repair (Open)',
    'EVAR (Endovascular Aneurysm Repair)',
    'Carotid Endarterectomy',
    'Femoral-Popliteal Bypass',
    'AV Fistula Formation',
    'Varicose Vein Surgery',
    'Embolectomy',
    'Amputation (Above Knee)',
    'Amputation (Below Knee)',
    
    # ENT
    'Tonsillectomy',
    'Adenoidectomy',
    'Septoplasty',
    'FESS (Functional Endoscopic Sinus Surgery)',
    'Microlaryngoscopy',
    'Panendoscopy',
    'Thyroidectomy',
    'Neck Dissection',
    'Myringotomy + Grommets',
    'Mastoidectomy',
    'Stapedectomy',
    'Submandibular Gland Excision',
    
    # Maxillofacial
    'Dental Extraction',
    'Wisdom Teeth Extraction',
    'Mandibular Fracture ORIF',
    'Le Fort Fracture Repair',
    'Zygoma Fracture ORIF',
    'TMJ Arthroscopy',
    
    # Plastics
    'Skin Graft',
    'Flap Surgery',
    'Carpal Tunnel Release',
    'Dupuytren\'s Contracture Release',
    'Hand Fracture ORIF',
    'Burn Debridement',
    'Breast Reconstruction',
    'Cleft Lip Repair',
    'Cleft Palate Repair',
    
    # Neurosurgery
    'Craniotomy',
    'Craniectomy',
    'Burr Holes',
    'EVD Insertion',
    'VP Shunt',
    'Spinal Decompression',
    'Acoustic Neuroma Excision',
    'Pituitary Surgery',
    
    # Cardiothoracic
    'CABG (Coronary Artery Bypass Graft)',
    'Valve Replacement',
    'Valve Repair',
    'ASD Closure',
    'VSD Closure',
    'Lobectomy',
    'Pneumonectomy',
    'VATS (Video-Assisted Thoracoscopic Surgery)',
    'Mediastinoscopy',
    'Pleurodesis',
    'Chest Drain Insertion',
    
    # Paediatric
    'Circumcision',
    'Herniotomy',
    'Orchidopexy',
    'Hypospadias Repair',
    'Pyloromyotomy',
    'Intussusception Reduction',
    'Appendicectomy',
]

ALL_PROCEDURES = COMMON_PROCEDURES + SURGICAL_PROCEDURES

EPA_OPTIONS = [
    'EPA1 - Initial Assessment & Management',
    'EPA2 - Pre-operative Assessment',
    'EPA3 - Safe Conduct of Anaesthesia',
    'EPA4 - Peri-operative Care',
    'EPA5 - Managing Acute Pain',
    'EPA6 - Resuscitation & Transfer',
    'EPA7 - General & Communication Skills'
]

AGE_CATEGORIES = [
    'Neonate (0-28d)',
    'Infant (1m-1y)',
    'Child (1-12y)',
    'Adolescent (12-18y)',
    'Adult (18-65y)',
    'Elderly (65+y)'
]

ASA_GRADES = ['1', '2', '3', '4', '5', '6', '1E', '2E', '3E', '4E', '5E']

ASSESSMENT_TYPES = {
    'case': 'Clinical Case',
    'cbd': 'CBD - Case-Based Discussion',
    'cex': 'CEX - Clinical Evaluation Exercise',
    'dops': 'DOPS - Direct Observation of Procedural Skills',
    'acat': 'ACAT - Acute Care Assessment Tool',
    'sle': 'Other SLE'
}

CBD_AREAS = [
    'Clinical Assessment',
    'Investigation & Referral',
    'Treatment & Management',
    'Clinical Judgement',
    'Communication',
    'Professionalism',
    'Organisation & Planning'
]

CEX_AREAS = [
    'History Taking',
    'Physical Examination',
    'Communication Skills',
    'Clinical Judgement',
    'Professionalism',
    'Organisation & Efficiency',
    'Overall Clinical Care'
]

REFLECTION_TEMPLATES = {
    'Emergency - Trauma': 'Assessed trauma patient in ED. Key considerations included potential difficult airway, hypovolaemia, and full stomach. Prepared for RSI with appropriate pre-oxygenation and blood products available. Discussed plan with consultant before proceeding.',
    'RSI': 'Performed RSI for emergency case. Ensured adequate pre-oxygenation, positioning, and preparation for failed intubation (CICO plan ready). Used appropriate induction agents considering haemodynamic status. Successful first-pass intubation with grade [X] view.',
    'Pre-operative Assessment': 'Conducted pre-operative assessment for emergency list patient. Assessed airway, cardiovascular and respiratory risk. Discussed anaesthetic plan with patient including risks/benefits. Documented clearly and communicated plan to theatre team.',
    'Spinal': 'Performed spinal anaesthetic for [procedure]. Ensured sterile technique, appropriate positioning, and monitoring. Discussed risks with patient. Achieved successful placement with good block height. Managed haemodynamic changes appropriately.',
    'Failed Intubation': 'Encountered difficult/failed intubation. Followed DAS guidelines - declared failed intubation, called for help, maintained oxygenation. Used [technique] successfully. Team worked well, patient safety maintained throughout. Debriefed afterwards.'
}

LEARNING_TEMPLATES = {
    'Emergency - Trauma': 'Reinforced importance of systematic ATLS approach, preparation for difficult airway, and clear communication with trauma team. Reviewed massive transfusion protocols.',
    'RSI': 'Consolidated RSI technique including optimal positioning, pre-oxygenation methods, and backup planning. Reviewed drug doses and indications for different clinical scenarios.',
    'Pre-operative Assessment': 'Enhanced skills in risk stratification and anaesthetic planning. Improved communication of complex information to patients under time pressure.',
    'Spinal': 'Developed technical skills in neuraxial techniques. Better understanding of contraindications, block assessment, and management of hypotension.',
    'Failed Intubation': 'Valuable learning on crisis resource management, following algorithms under pressure, and importance of early escalation. Reviewed DAS guidelines in detail afterwards.'
}

# Functions
def call_claude_api(prompt, max_tokens=1000):
    """Call Claude API to help generate content"""
    api_key = st.session_state.get('anthropic_api_key', '')
    
    if not api_key:
        return "⚠️ Please enter your Anthropic API key in the AI Assistant section to use this feature."
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
                "x-api-key": api_key
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": max_tokens,
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['content'][0]['text']
        elif response.status_code == 401:
            return "❌ Invalid API key. Please check your key and try again."
        elif response.status_code == 429:
            return "⚠️ Rate limit reached. Please wait a moment and try again."
        else:
            return f"❌ Error {response.status_code}: {response.text}"
    except requests.exceptions.Timeout:
        return "⚠️ Request timed out. Please check your internet connection and try again."
    except Exception as e:
        return f"❌ Error: {str(e)}"

def generate_reflection_prompt(case_data):
    """Generate a prompt for Claude to help write reflection"""
    prompt = f"""I'm an anaesthetic CT1 trainee documenting a case for my portfolio. Can you help me write a reflection?

Case details:
- Type: {case_data.get('case_type', 'Not specified')}
- Procedure: {case_data.get('procedure', 'Not specified')}
- Patient: {case_data.get('age_category', 'Not specified')}, ASA {case_data.get('asa_grade', 'Not specified')}
- Notes: {case_data.get('notes', 'Not specified')}

Please write a concise clinical reflection (3-4 sentences) covering:
1. What happened and what I did
2. Key clinical decisions or considerations
3. Any challenges or interesting aspects

Keep it professional and suitable for a portfolio."""
    return prompt

def generate_learning_prompt(case_data):
    """Generate a prompt for Claude to help write learning points"""
    prompt = f"""I'm an anaesthetic CT1 trainee documenting a case for my portfolio. Can you help me write learning points?

Case details:
- Type: {case_data.get('case_type', 'Not specified')}
- Procedure: {case_data.get('procedure', 'Not specified')}
- Patient: {case_data.get('age_category', 'Not specified')}, ASA {case_data.get('asa_grade', 'Not specified')}
- Notes: {case_data.get('notes', 'Not specified')}
- Reflection: {case_data.get('reflection', 'Not specified')}

Please write 2-3 specific learning points covering:
1. What I learned or consolidated
2. What I'd do differently or what to review
3. Practical takeaways for future cases

Keep it concise and actionable."""
    return prompt

def get_current_time_of_day():
    """Get current time of day based on hour"""
    from datetime import datetime
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return 'Morning'
    elif 12 <= hour < 17:
        return 'Afternoon'
    elif 17 <= hour < 21:
        return 'Evening'
    else:
        return 'Night'

def save_data():
    """Save cases to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(st.session_state.cases, f, indent=2)

def add_case(case_data):
    """Add or update a case"""
    if st.session_state.editing_id is not None:
        # Update existing case
        for i, case in enumerate(st.session_state.cases):
            if case['id'] == st.session_state.editing_id:
                st.session_state.cases[i] = {**case_data, 'id': st.session_state.editing_id}
                break
        st.session_state.editing_id = None
    else:
        # Add new case
        case_data['id'] = int(datetime.now().timestamp() * 1000)
        st.session_state.cases.append(case_data)
    
    save_data()
    st.session_state.show_form = False

def delete_case(case_id):
    """Delete a case"""
    st.session_state.cases = [c for c in st.session_state.cases if c['id'] != case_id]
    save_data()

def toggle_complete(case_id):
    """Toggle case completion status"""
    for case in st.session_state.cases:
        if case['id'] == case_id:
            case['completed'] = not case.get('completed', False)
            break
    save_data()

def toggle_exported(case_id):
    """Toggle case exported status - NEW FUNCTION"""
    for case in st.session_state.cases:
        if case['id'] == case_id:
            case['exported'] = not case.get('exported', False)
            break
    save_data()

def export_cases(cases_to_export):
    """Export cases to text format"""
    output = []
    for case in cases_to_export:
        output.append(format_case_for_export(case))
    return '\n'.join(output)

def format_case_for_export(case):
    """Format a single case for export optimized for LLP copy/paste"""
    lines = []
    
    # Title section - clear and concise
    lines.append("=" * 70)
    assessment_label = ASSESSMENT_TYPES.get(case.get('assessment_type', 'case'), 'Clinical Case')
    lines.append(f"{assessment_label.upper()}")
    lines.append("=" * 70)
    
    # Core case details in LLP-friendly format
    lines.append("")
    lines.append("CASE DETAILS")
    lines.append("-" * 70)
    
    # Date/Time
    if case.get('date'):
        date_display = case['date']
        if case.get('time'):
            date_display += f" ({case['time']})"
        lines.append(f"Date: {date_display}")
    
    # Patient info (anonymized as LLP requires)
    patient_info = []
    if case.get('age_category'):
        patient_info.append(f"Age: {case['age_category']}")
    if case.get('asa_grade'):
        patient_info.append(f"ASA: {case['asa_grade']}")
    if patient_info:
        lines.append(", ".join(patient_info))
    
    # Case classification
    if case.get('urgency'):
        lines.append(f"Urgency: {case['urgency']}")
    
    if case.get('operation_type'):
        lines.append(f"Specialty: {case['operation_type']}")
    
    if case.get('anaesthetic_type'):
        lines.append(f"Anaesthetic: {case['anaesthetic_type']}")
    
    if case.get('supervision_level'):
        lines.append(f"Role/Supervision: {case['supervision_level']}")
    
    # Procedure
    if case.get('procedure'):
        lines.append(f"Procedure: {case['procedure']}")
    
    # Supervisor
    if case.get('supervisor'):
        lines.append(f"Supervisor: {case['supervisor']}")
    
    # Clinical notes
    if case.get('notes'):
        lines.append("")
        lines.append("CLINICAL NOTES")
        lines.append("-" * 70)
        lines.append(case['notes'])
    
    # Assessment-specific sections
    if case.get('cbd_scores'):
        has_scores = any(score for score in case['cbd_scores'].values())
        if has_scores:
            lines.append("")
            lines.append("CBD COMPETENCY RATINGS")
            lines.append("-" * 70)
            for area, score in case['cbd_scores'].items():
                if score:
                    lines.append(f"{area}: {score}")
    
    if case.get('cex_scores'):
        has_scores = any(score for score in case['cex_scores'].values())
        if has_scores:
            lines.append("")
            lines.append("CEX COMPETENCY RATINGS")
            lines.append("-" * 70)
            for area, score in case['cex_scores'].items():
                if score:
                    lines.append(f"{area}: {score}")
    
    # Reflection (key for portfolio)
    if case.get('reflection'):
        lines.append("")
        lines.append("REFLECTION")
        lines.append("-" * 70)
        lines.append(case['reflection'])
    
    # Learning points (key for portfolio)
    if case.get('learning'):
        lines.append("")
        lines.append("LEARNING POINTS")
        lines.append("-" * 70)
        lines.append(case['learning'])
    
    # EPA/SLE links (important for curriculum mapping)
    if case.get('linked_to'):
        lines.append("")
        lines.append("CURRICULUM LINKS")
        lines.append("-" * 70)
        for epa in case['linked_to']:
            lines.append(f"• {epa}")
    
    lines.append("")
    lines.append("=" * 70)
    lines.append("")
    
    return '\n'.join(lines)

def get_stats():
    """Calculate statistics"""
    total = len(st.session_state.cases)
    complete = sum(1 for c in st.session_state.cases if c.get('completed', False))
    incomplete = total - complete
    
    # Cases this week
    today = datetime.now()
    week_ago = datetime.now().timestamp() - (7 * 24 * 60 * 60)
    this_week = sum(1 for c in st.session_state.cases 
                    if datetime.strptime(c['date'], '%Y-%m-%d').timestamp() >= week_ago)
    
    return {
        'total': total,
        'complete': complete,
        'incomplete': incomplete,
        'this_week': this_week
    }

# Main UI
st.title("🏥 Anaesthetic Case Logger")
st.markdown("*Quick capture for portfolio documentation*")

# Add logout button in header
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("🔓 Logout"):
        st.session_state.authenticated = False
        st.rerun()

# Info about AI helper
with st.expander("ℹ️ About the AI Helper"):
    st.markdown("""
    **🤖 Claude AI Integration**
    
    The AI helper can generate professional reflections and learning points for your cases.
    
    **Setup (one-time):**
    1. Get a free API key from [console.anthropic.com](https://console.anthropic.com)
    2. Enter it in the "🤖 AI Assistant" section when adding a case
    3. Your key is stored locally in your browser session (not saved permanently)
    
    **How to use:**
    - Describe your case and add notes in the AI helper
    - Click "Generate Reflection" or "Generate Learning Points"
    - Copy the output and paste into your case form
    - Edit to personalize
    
    **Perfect for:**
    - Getting started when you're stuck
    - Ensuring you've covered key points
    - Saving time on routine documentation
    
    **Note:** API calls use your Anthropic credits (very cheap - fractions of a penny per case)
    """)

# Assessment type selector
st.markdown("### 📋 What would you like to log?")
cols = st.columns(len(ASSESSMENT_TYPES))
for idx, (key, label) in enumerate(ASSESSMENT_TYPES.items()):
    with cols[idx]:
        if st.button(label, use_container_width=True, type="primary" if st.session_state.assessment_type == key else "secondary"):
            st.session_state.assessment_type = key
            st.rerun()

st.markdown("---")

# Statistics
stats = get_stats()
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; color: white; text-align: center;">
        <div style="font-size: 2.5rem; font-weight: bold;">{stats['total']}</div>
        <div style="font-size: 0.9rem; opacity: 0.9;">Total Cases</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #10b981 0%, #059669 100%); padding: 1.5rem; border-radius: 10px; color: white; text-align: center;">
        <div style="font-size: 2.5rem; font-weight: bold;">{stats['complete']}</div>
        <div style="font-size: 0.9rem; opacity: 0.9;">Complete</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 1.5rem; border-radius: 10px; color: white; text-align: center;">
        <div style="font-size: 2.5rem; font-weight: bold;">{stats['incomplete']}</div>
        <div style="font-size: 0.9rem; opacity: 0.9;">To Finish</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); padding: 1.5rem; border-radius: 10px; color: white; text-align: center;">
        <div style="font-size: 2.5rem; font-weight: bold;">{stats['this_week']}</div>
        <div style="font-size: 0.9rem; opacity: 0.9;">This Week</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# Controls
col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])

with col1:
    if st.button("📋 All Cases", use_container_width=True):
        st.session_state.filter = 'all'

with col2:
    if st.button(f"⏳ To Do ({stats['incomplete']})", use_container_width=True):
        st.session_state.filter = 'incomplete'

with col3:
    if st.button(f"✅ Done ({stats['complete']})", use_container_width=True):
        st.session_state.filter = 'complete'

with col4:
    if st.button("➕ Add Case", use_container_width=True, type="primary"):
        st.session_state.show_form = True
        st.session_state.editing_id = None

with col5:
    # Export button
    filter_type = st.session_state.get('filter', 'all')
    if filter_type == 'incomplete':
        cases_to_export = [c for c in st.session_state.cases if not c.get('completed', False)]
    elif filter_type == 'complete':
        cases_to_export = [c for c in st.session_state.cases if c.get('completed', False)]
    else:
        cases_to_export = st.session_state.cases
    
    if cases_to_export:
        export_text = export_cases(cases_to_export)
        st.download_button(
            label="📥 Export",
            data=export_text,
            file_name=f"cases_export_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )

st.markdown("---")

# Add/Edit Form
if st.session_state.show_form:
    with st.container():
        st.subheader("📝 New Case" if st.session_state.editing_id is None else "✏️ Edit Case")
        
        # Load existing case data if editing
        if st.session_state.editing_id is not None:
            existing_case = next((c for c in st.session_state.cases if c['id'] == st.session_state.editing_id), {})
        else:
            existing_case = {}
        
        # AI Helper Section (outside form)
        with st.expander("🤖 AI Assistant - Get Help Writing", expanded=False):
            st.info("**How to use:** Enter your Anthropic API key below, fill in case details (💡 Tip: Click in text fields and use your keyboard's voice input!), then generate text. Copy the AI output and paste it into the form fields.")
            
            # API Key input
            st.markdown("**🔑 API Key Setup**")
            col1, col2 = st.columns([3, 1])
            with col1:
                api_key_input = st.text_input(
                    "Anthropic API Key",
                    type="password",
                    value=st.session_state.get('anthropic_api_key', ''),
                    placeholder="sk-ant-...",
                    help="Get your API key from console.anthropic.com"
                )
                if api_key_input:
                    st.session_state['anthropic_api_key'] = api_key_input
            with col2:
                st.markdown("[Get API Key](https://console.anthropic.com)")
            
            if not st.session_state.get('anthropic_api_key'):
                st.warning("⚠️ Enter your API key above to use AI features. Don't have one? Click 'Get API Key' to sign up (free credits available).")
            else:
                st.success("✅ API key saved! AI features are ready to use.")
            
            st.markdown("---")
            st.markdown("**🎤 Voice Input Available!** On mobile: Tap text field → tap microphone on keyboard. On desktop: Use your OS voice input (Windows: Win+H, Mac: Fn twice)")
            
            st.text_input("What case are you documenting?", key="ai_case_summary", placeholder="e.g., 'Emergency laparotomy, ASA 3 patient, RSI done'")
            st.text_area("What are your key notes?", key="ai_notes_input", height=80, placeholder="Brief case details, challenges, what you did...")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✨ Generate Reflection", use_container_width=True):
                    if st.session_state.get('ai_case_summary') or st.session_state.get('ai_notes_input'):
                        with st.spinner("🤖 Claude is writing..."):
                            prompt = f"""I'm an anaesthetic CT1 trainee documenting: {st.session_state.get('ai_case_summary', 'a clinical case')}

Key details: {st.session_state.get('ai_notes_input', 'not specified')}

Write a concise professional reflection (3-4 sentences) covering what happened, clinical decisions, and any challenges."""
                            ai_text = call_claude_api(prompt)
                            st.success("✨ Generated Reflection:")
                            st.code(ai_text, language=None)
                            st.caption("Copy this text ☝️ and paste into the Reflection field below")
                    else:
                        st.warning("Please fill in case details above first!")
            
            with col2:
                if st.button("✨ Generate Learning Points", use_container_width=True):
                    if st.session_state.get('ai_case_summary') or st.session_state.get('ai_notes_input'):
                        with st.spinner("🤖 Claude is writing..."):
                            prompt = f"""I'm an anaesthetic CT1 trainee documenting: {st.session_state.get('ai_case_summary', 'a clinical case')}

Key details: {st.session_state.get('ai_notes_input', 'not specified')}

Write 2-3 specific learning points: what I learned, what to review, practical takeaways."""
                            ai_text = call_claude_api(prompt)
                            st.success("✨ Generated Learning Points:")
                            st.code(ai_text, language=None)
                            st.caption("Copy this text ☝️ and paste into the Learning Points field below")
                    else:
                        st.warning("Please fill in case details above first!")
            
            st.markdown("---")
            st.markdown("**💬 Ask a Custom Question**")
            custom_q = st.text_area("Your question about this case:", height=60, key="custom_question_input", 
                                   placeholder="e.g., 'What are the key complications?' or 'What guidelines should I read?'")
            if st.button("🤖 Ask Claude", use_container_width=True):
                if custom_q:
                    with st.spinner("🤖 Thinking..."):
                        prompt = f"""I'm an anaesthetic CT1 trainee. Case: {st.session_state.get('ai_case_summary', 'not specified')}
Details: {st.session_state.get('ai_notes_input', 'not specified')}

Question: {custom_q}

Provide a helpful, concise answer for my training level."""
                        ai_answer = call_claude_api(prompt, max_tokens=600)
                        st.success("🤖 Claude's Answer:")
                        st.write(ai_answer)
                else:
                    st.warning("Please enter a question!")
        
        # Specialty selector OUTSIDE form for dynamic updates
        st.markdown("---")
        st.markdown("**🏥 Select Surgical Specialty** (this will filter the procedure dropdown below)")
        
        # Get existing specialty if editing
        existing_specialty = ''
        if st.session_state.editing_id:
            existing_case = next((c for c in st.session_state.cases if c['id'] == st.session_state.editing_id), {})
            existing_specialty = existing_case.get('operation_type', '')
        
        specialty = st.selectbox(
            "Surgical Specialty",
            [''] + SPECIALTIES + ['Anaesthetic Procedure', 'Other'],
            index=SPECIALTIES.index(existing_specialty) + 1 if existing_specialty in SPECIALTIES else (
                len(SPECIALTIES) + 1 if existing_specialty == 'Anaesthetic Procedure' else (
                    len(SPECIALTIES) + 2 if existing_specialty == 'Other' else 0
                )
            ),
            help="Select specialty to filter procedures below",
            key="specialty_selector"
        )
        
        # Store in session state for use in form
        st.session_state['selected_specialty'] = specialty
        
        # Show which procedures will be available
        if specialty == 'Anaesthetic Procedure':
            st.info(f"📋 Procedure dropdown will show: Anaesthetic procedures (lines, blocks, airway management)")
        elif specialty and specialty != 'Other' and specialty in PROCEDURES_BY_SPECIALTY:
            num_procs = len(PROCEDURES_BY_SPECIALTY[specialty])
            st.info(f"📋 Procedure dropdown will show: {num_procs} {specialty} procedures")
        elif specialty == 'Other':
            st.info(f"📋 Procedure dropdown will show: All 170+ procedures")
        else:
            st.warning("⚠️ Please select a specialty above to see available procedures")
        
        with st.form("case_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                case_date = st.date_input(
                    "Date",
                    value=datetime.strptime(existing_case.get('date', date.today().isoformat()), '%Y-%m-%d').date()
                )
            
            with col2:
                # Auto-fill time of day if new case
                default_time = existing_case.get('time', '') if existing_case.get('time') else get_current_time_of_day()
                time_of_day = st.selectbox(
                    "Time of Day",
                    TIME_OF_DAY,
                    index=TIME_OF_DAY.index(default_time) if default_time in TIME_OF_DAY else 0
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                age_category = st.text_input(
                    "Patient Age",
                    value=existing_case.get('age_category', ''),
                    placeholder="e.g., 45y, 6m, 3 weeks"
                )
            
            with col2:
                asa_grade = st.selectbox(
                    "ASA Grade",
                    [''] + ASA_GRADES,
                    index=ASA_GRADES.index(existing_case.get('asa_grade', '')) + 1 if existing_case.get('asa_grade') in ASA_GRADES else 0
                )
            
            col1, col2 = st.columns(2)
            
            with col1:
                urgency = st.selectbox(
                    "Urgency",
                    [''] + URGENCY_TYPES,
                    index=URGENCY_TYPES.index(existing_case.get('urgency', '')) + 1 if existing_case.get('urgency') in URGENCY_TYPES else 0
                )
            
            with col2:
                # Use specialty from session state (selected outside form)
                specialty = st.session_state.get('selected_specialty', '')
                operation_type = specialty
                
                # Show selected specialty (read-only)
                st.markdown("**Surgical Specialty**")
                specialty_display = specialty if specialty else "(Select above form)"
                st.info(f"Selected: **{specialty_display}**")
            
            anaesthetic_type = st.selectbox(
                "Anaesthetic Type",
                [''] + ANAESTHETIC_TYPES,
                index=ANAESTHETIC_TYPES.index(existing_case.get('anaesthetic_type', '')) + 1 if existing_case.get('anaesthetic_type') in ANAESTHETIC_TYPES else 0
            )
            
            supervision_level = st.selectbox(
                "Your Role / Supervision Level",
                [''] + SUPERVISION_LEVELS,
                index=SUPERVISION_LEVELS.index(existing_case.get('supervision_level', '')) + 1 if existing_case.get('supervision_level') in SUPERVISION_LEVELS else 0
            )
            
            case_type = st.selectbox(
                "Case Type (optional)",
                [''] + CASE_TYPES,
                index=CASE_TYPES.index(existing_case.get('case_type', '')) + 1 if existing_case.get('case_type') in CASE_TYPES else 0
            )
            
            # Procedure dropdown - filtered by specialty
            st.markdown("**Procedure Performed**")
            
            # Determine which procedures to show based on specialty
            if specialty == 'Anaesthetic Procedure':
                available_procedures = COMMON_PROCEDURES
                help_text = "Anaesthetic procedures (lines, blocks, etc.)"
            elif specialty and specialty != 'Other' and specialty in PROCEDURES_BY_SPECIALTY:
                available_procedures = PROCEDURES_BY_SPECIALTY[specialty]
                help_text = f"Procedures filtered for {specialty}"
            elif specialty == 'Other':
                available_procedures = ALL_SURGICAL_PROCEDURES
                help_text = "All surgical procedures - please select specialty above to filter"
            else:
                # No specialty selected - show limited options
                available_procedures = ['Please select a specialty first']
                help_text = "Select a specialty above to see procedures"
            
            # Sort and add to dropdown
            if available_procedures != ['Please select a specialty first']:
                available_procedures = sorted(available_procedures)
            
            procedure = st.selectbox(
                "Select or type procedure (searchable)",
                [''] + available_procedures + ['Other (type below)'],
                index=available_procedures.index(existing_case.get('procedure', '')) + 1 if existing_case.get('procedure') in available_procedures else 0,
                label_visibility="collapsed",
                help=help_text
            )
            
            # If "Other" selected or typing custom, show text input
            if procedure == 'Other (type below)' or procedure == 'Please select a specialty first':
                procedure = st.text_input(
                    "Enter procedure name",
                    value=existing_case.get('procedure', '') if existing_case.get('procedure') not in available_procedures else '',
                    placeholder="Type procedure name",
                    label_visibility="collapsed"
                )
            
            supervisor = st.text_input(
                "Supervisor",
                value=existing_case.get('supervisor', ''),
                placeholder="e.g., Dr Smith, ST6 Dan"
            )
            
            notes = st.text_area(
                "Quick Notes",
                value=existing_case.get('notes', ''),
                placeholder="Brief case details, patient factors, any challenges...",
                height=100
            )
            
            # Initialize assessment-specific scores
            cbd_scores = {}
            cex_scores = {}
            
            # Assessment-specific fields
            if st.session_state.assessment_type == 'cbd':
                st.markdown("**CBD Competency Areas**")
                cbd_scores = existing_case.get('cbd_scores', {})
                cols = st.columns(2)
                for idx, area in enumerate(CBD_AREAS):
                    with cols[idx % 2]:
                        cbd_scores[area] = st.selectbox(
                            area,
                            ['', 'Below expectations', 'Meets expectations', 'Above expectations', 'Excellent'],
                            index=['', 'Below expectations', 'Meets expectations', 'Above expectations', 'Excellent'].index(cbd_scores.get(area, '')) if cbd_scores.get(area) else 0,
                            key=f"cbd_{area}"
                        )
            
            elif st.session_state.assessment_type == 'cex':
                st.markdown("**CEX Competency Areas**")
                cex_scores = existing_case.get('cex_scores', {})
                cols = st.columns(2)
                for idx, area in enumerate(CEX_AREAS):
                    with cols[idx % 2]:
                        cex_scores[area] = st.selectbox(
                            area,
                            ['', '1 - Below expectations', '2 - Borderline', '3 - Meets expectations', '4 - Above expectations', '5 - Excellent'],
                            index=['', '1 - Below expectations', '2 - Borderline', '3 - Meets expectations', '4 - Above expectations', '5 - Excellent'].index(cex_scores.get(area, '')) if cex_scores.get(area) else 0,
                            key=f"cex_{area}"
                        )
            
            # Reflection with template
            st.markdown("**Reflection**")
            col1, col2 = st.columns([4, 1])
            with col2:
                use_reflection_template = st.checkbox("Use Template", key="reflection_template")
            
            template_key = case_type if case_type in REFLECTION_TEMPLATES else procedure
            default_reflection = REFLECTION_TEMPLATES.get(template_key, '') if use_reflection_template else existing_case.get('reflection', '')
            
            reflection = st.text_area(
                "reflection_text",
                value=default_reflection,
                placeholder="What happened, what you did, clinical decision-making... (Use AI Assistant above for help)",
                height=150,
                label_visibility="collapsed"
            )
            
            # Learning with template
            st.markdown("**Learning Points**")
            col1, col2 = st.columns([4, 1])
            with col2:
                use_learning_template = st.checkbox("Use Template", key="learning_template")
            
            default_learning = LEARNING_TEMPLATES.get(template_key, '') if use_learning_template else existing_case.get('learning', '')
            
            learning = st.text_area(
                "learning_text",
                value=default_learning,
                placeholder="What did you learn? What would you do differently? What will you read up on? (Use AI Assistant above for help)",
                height=100,
                label_visibility="collapsed"
            )
            
            st.markdown("**Link to EPAs/SLEs**")
            
            # Show EPA suggestions for assessments (not clinical cases)
            if st.session_state.assessment_type != 'case':
                suggested_epas = []
                assessment_type = st.session_state.assessment_type
                
                # Get suggestions based on procedure and notes
                search_text = (procedure + ' ' + notes).lower()
                
                if assessment_type in EPA_SUGGESTIONS:
                    suggestions_map = EPA_SUGGESTIONS[assessment_type]
                    
                    # Check for keywords
                    for keyword, epas in suggestions_map.items():
                        if keyword in search_text:
                            suggested_epas.extend(epas)
                    
                    # If no matches, use default
                    if not suggested_epas and 'default' in suggestions_map:
                        suggested_epas = suggestions_map['default']
                    
                    # Remove duplicates
                    suggested_epas = list(dict.fromkeys(suggested_epas))
                    
                    if suggested_epas:
                        st.info(f"💡 **Suggested EPAs based on this {assessment_type.upper()}:** {', '.join(suggested_epas)}")
            
            linked_to = []
            cols = st.columns(2)
            for idx, epa in enumerate(EPA_OPTIONS):
                with cols[idx % 2]:
                    if st.checkbox(epa, value=epa in existing_case.get('linked_to', []), key=f"epa_{idx}"):
                        linked_to.append(epa)
            
            completed = st.checkbox("Mark as complete", value=existing_case.get('completed', False))
            
            col1, col2 = st.columns([3, 1])
            with col1:
                submit = st.form_submit_button(
                    "💾 Save Case" if st.session_state.editing_id is None else "💾 Update Case",
                    use_container_width=True,
                    type="primary"
                )
            with col2:
                cancel = st.form_submit_button("Cancel", use_container_width=True)
            
            if submit:
                case_data = {
                    'assessment_type': st.session_state.assessment_type,
                    'date': case_date.isoformat(),
                    'time': time_of_day,
                    'age_category': age_category,
                    'asa_grade': asa_grade,
                    'urgency': urgency,
                    'operation_type': operation_type,
                    'anaesthetic_type': anaesthetic_type,
                    'supervision_level': supervision_level,
                    'case_type': case_type,
                    'procedure': procedure,
                    'supervisor': supervisor,
                    'notes': notes,
                    'reflection': reflection,
                    'learning': learning,
                    'linked_to': linked_to,
                    'completed': completed,
                    'exported': existing_case.get('exported', False)  # Preserve exported status
                }
                
                # Add assessment-specific scores
                if st.session_state.assessment_type == 'cbd':
                    case_data['cbd_scores'] = cbd_scores
                elif st.session_state.assessment_type == 'cex':
                    case_data['cex_scores'] = cex_scores
                
                add_case(case_data)
                st.rerun()
            
            if cancel:
                st.session_state.show_form = False
                st.session_state.editing_id = None
                st.rerun()

st.markdown("---")

# Display cases
filter_type = st.session_state.get('filter', 'all')
filtered_cases = st.session_state.cases.copy()

if filter_type == 'incomplete':
    filtered_cases = [c for c in filtered_cases if not c.get('completed', False)]
elif filter_type == 'complete':
    filtered_cases = [c for c in filtered_cases if c.get('completed', False)]

# Sort by date (most recent first)
filtered_cases.sort(key=lambda x: x['date'], reverse=True)

if not filtered_cases:
    st.info("📋 No cases to display. Start by adding your first case above!")
else:
    for case in filtered_cases:
        # IMPROVED: Ensure consistent display for ALL case types
        # Create a clean case card using native Streamlit components
        card_color = "#f0f0f0" if case.get('completed', False) else "#ffffff"
        border_color = "#10b981" if case.get('completed', False) else "#667eea"
        
        with st.container():
            col1, col2 = st.columns([5, 1])
            
            with col1:
                # Date and badges
                status_badges = []
                if case.get('completed', False):
                    status_badges.append("✅ Complete")
                else:
                    status_badges.append("⏳ To Finish")
                
                # NEW: Add exported badge
                if case.get('exported', False):
                    status_badges.append("📥 Exported")
                
                assessment_label = ASSESSMENT_TYPES.get(case.get('assessment_type', 'case'), 'Clinical Case')
                
                date_display = case['date']
                if case.get('time'):
                    date_display += f" ({case.get('time')})"
                
                badges_text = " &nbsp;&nbsp; ".join(status_badges)
                st.markdown(f"**{date_display}** &nbsp;&nbsp; {badges_text} &nbsp;&nbsp; *{assessment_label}*")
                
                # IMPROVED: Always show procedure/title prominently for ALL case types
                procedure_display = case.get('procedure', 'Procedure not specified')
                st.markdown(f"### {procedure_display}")
                
                # Case details in a clean line
                details = []
                if case.get('urgency'):
                    details.append(case['urgency'])
                if case.get('operation_type'):
                    details.append(case['operation_type'])
                if case.get('anaesthetic_type'):
                    details.append(case['anaesthetic_type'])
                if case.get('age_category'):
                    details.append(case['age_category'])
                if case.get('asa_grade'):
                    details.append(f"ASA {case['asa_grade']}")
                
                if details:
                    st.markdown(" • ".join(details))
                
                # Supervision and supervisor
                supervision_line = []
                if case.get('supervision_level'):
                    supervision_line.append(case['supervision_level'])
                if case.get('supervisor'):
                    supervision_line.append(case['supervisor'])
                
                if supervision_line:
                    st.caption(" • ".join(supervision_line))
            
            with col2:
                # IMPROVED: Add exported toggle button
                col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
                with col_a:
                    if st.button("✓", key=f"complete_{case['id']}", help="Toggle complete"):
                        toggle_complete(case['id'])
                        st.rerun()
                with col_b:
                    # NEW: Exported toggle button
                    exported_icon = "📥" if case.get('exported', False) else "⬜"
                    if st.button(exported_icon, key=f"export_toggle_{case['id']}", help="Mark as exported"):
                        toggle_exported(case['id'])
                        st.rerun()
                with col_c:
                    if st.button("✏️", key=f"edit_{case['id']}", help="Edit case"):
                        st.session_state.editing_id = case['id']
                        st.session_state.show_form = True
                        st.rerun()
                with col_d:
                    if st.button("📋", key=f"duplicate_{case['id']}", help="Duplicate case"):
                        # Create a duplicate with new ID and date
                        duplicate = case.copy()
                        duplicate['id'] = int(datetime.now().timestamp() * 1000)
                        duplicate['date'] = date.today().isoformat()
                        duplicate['completed'] = False
                        duplicate['exported'] = False  # Reset exported status
                        st.session_state.cases.append(duplicate)
                        save_data()
                        st.success("Case duplicated! Edit the new case to update details.")
                        st.rerun()
                with col_e:
                    # Export this case button
                    case_export = format_case_for_export(case)
                    st.download_button(
                        label="📄",
                        data=case_export,
                        file_name=f"case_{case['date']}_{case.get('procedure', 'case').replace(' ', '_')}.txt",
                        mime="text/plain",
                        key=f"export_{case['id']}",
                        help="Export this case"
                    )
                with col_f:
                    if st.button("🗑️", key=f"delete_{case['id']}", help="Delete case"):
                        delete_case(case['id'])
                        st.rerun()
            
            # IMPROVED: Always show expandable details for ALL cases
            with st.expander("View Details"):
                # Quick copy section at top
                st.markdown("**📋 Quick Copy for LLP (Lifelong Learning Platform):**")
                st.info("💡 **Tip:** Copy this formatted text and paste directly into LLP's reflection/notes fields. Sections are clearly labeled for easy reference.")
                case_export = format_case_for_export(case)
                st.text_area(
                    "Copy this text to your ePortfolio:",
                    value=case_export,
                    height=250,
                    key=f"copy_area_{case['id']}"
                )
                st.caption("👆 Click in box → Ctrl+A (select all) → Ctrl+C (copy) → Paste into LLP")
                
                st.markdown("---")
                
                if case.get('notes'):
                    st.markdown("**Notes:**")
                    st.info(case['notes'])
                
                # Display CBD scores if present
                if case.get('cbd_scores'):
                    st.markdown("**CBD Competency Scores:**")
                    for area, score in case['cbd_scores'].items():
                        if score:
                            st.write(f"• {area}: {score}")
                
                # Display CEX scores if present
                if case.get('cex_scores'):
                    st.markdown("**CEX Competency Scores:**")
                    for area, score in case['cex_scores'].items():
                        if score:
                            st.write(f"• {area}: {score}")
                
                if case.get('reflection'):
                    st.markdown("**Reflection:**")
                    st.success(case['reflection'])
                
                if case.get('learning'):
                    st.markdown("**Learning:**")
                    st.warning(case['learning'])
                
                if case.get('linked_to'):
                    st.markdown("**Linked to:**")
                    for epa in case['linked_to']:
                        st.markdown(f'<span class="epa-tag">{epa}</span>', unsafe_allow_html=True)
            
            # Add separator line between cases
            st.markdown("---")

# MCQ Generator Section
st.markdown("---")
with st.expander("📝 Generate Practice MCQs from Your Cases"):
    generate_mcqs_from_cases()

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 0.875rem; padding: 1rem;">
    Data stored locally in case_logger_data.json. Export regularly to backup your cases.
</div>
""", unsafe_allow_html=True)

