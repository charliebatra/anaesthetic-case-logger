import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os
import requests

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
        
        with st.form("case_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                case_date = st.date_input(
                    "Date",
                    value=datetime.strptime(existing_case.get('date', date.today().isoformat()), '%Y-%m-%d').date()
                )
            
            with col2:
                time_of_day = st.selectbox(
                    "Time of Day",
                    [''] + TIME_OF_DAY,
                    index=TIME_OF_DAY.index(existing_case.get('time', '')) + 1 if existing_case.get('time') in TIME_OF_DAY else 0
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
                operation_type = st.selectbox(
                    "Operation Type",
                    [''] + OPERATION_TYPES,
                    index=OPERATION_TYPES.index(existing_case.get('operation_type', '')) + 1 if existing_case.get('operation_type') in OPERATION_TYPES else 0
                )
            
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
            
            # Procedure with both dropdown suggestions and freetext
            st.markdown("**Procedure Performed**")
            col1, col2 = st.columns([1, 3])
            with col1:
                use_common_procedure = st.checkbox("Use common", value=existing_case.get('procedure') in COMMON_PROCEDURES if existing_case.get('procedure') else False, key="use_common_proc")
            
            if use_common_procedure:
                procedure = st.selectbox(
                    "Select procedure",
                    [''] + COMMON_PROCEDURES,
                    index=COMMON_PROCEDURES.index(existing_case.get('procedure', '')) + 1 if existing_case.get('procedure') in COMMON_PROCEDURES else 0,
                    label_visibility="collapsed"
                )
            else:
                procedure = st.text_input(
                    "Enter procedure",
                    value=existing_case.get('procedure', '') if existing_case.get('procedure') not in COMMON_PROCEDURES else '',
                    placeholder="e.g., Emergency laparotomy for perforated bowel",
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
                    'completed': completed
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
        with st.container():
            # Case card
            card_class = "case-card case-complete" if case.get('completed', False) else "case-card"
            
            col1, col2 = st.columns([4, 1])
            
            with col1:
                status_badge = "complete" if case.get('completed', False) else "incomplete"
                status_text = "Complete" if case.get('completed', False) else "To Finish"
                assessment_label = ASSESSMENT_TYPES.get(case.get('assessment_type', 'case'), 'Clinical Case')
                
                st.markdown(f"""
                <div class="{card_class}">
                    <div style="margin-bottom: 0.5rem;">
                        <span style="color: #667eea; font-weight: 600; font-size: 0.9rem;">
                            {case['date']}{' (' + case.get('time', '') + ')' if case.get('time') else ''}
                        </span>
                        <span class="badge badge-{status_badge}">{status_text}</span>
                        <span style="background: #e0e7ff; color: #3730a3; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; margin-left: 0.5rem;">
                            {assessment_label}
                        </span>
                    </div>
                    <h3 style="margin: 0.5rem 0; font-size: 1.25rem; color: #1f2937;">
                        {case.get('procedure', 'Unknown Procedure')}
                    </h3>
                    <p style="color: #6b7280; font-size: 0.9rem; margin: 0.25rem 0;">
                        {case.get('urgency', '')}{'  •  ' if case.get('urgency') and case.get('operation_type') else ''}{case.get('operation_type', '')}
                        {' • ' if case.get('anaesthetic_type') and (case.get('urgency') or case.get('operation_type')) else ''}{case.get('anaesthetic_type', '')}
                        {' • ' if (case.get('urgency') or case.get('operation_type') or case.get('anaesthetic_type')) and case.get('age_category') else ''}{case.get('age_category', '')} • ASA {case.get('asa_grade', '')}
                    </p>
                    <p style="color: #6b7280; font-size: 0.85rem; margin: 0.25rem 0; font-style: italic;">
                        {case.get('supervision_level', '')}{' • ' if case.get('supervision_level') and case.get('supervisor') else ''}{case.get('supervisor', '')}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                col_a, col_b, col_c, col_d, col_e = st.columns(5)
                with col_a:
                    if st.button("✓", key=f"complete_{case['id']}", help="Toggle complete"):
                        toggle_complete(case['id'])
                        st.rerun()
                with col_b:
                    if st.button("✏️", key=f"edit_{case['id']}", help="Edit case"):
                        st.session_state.editing_id = case['id']
                        st.session_state.show_form = True
                        st.rerun()
                with col_c:
                    if st.button("📋", key=f"duplicate_{case['id']}", help="Duplicate case"):
                        # Create a duplicate with new ID and date
                        duplicate = case.copy()
                        duplicate['id'] = int(datetime.now().timestamp() * 1000)
                        duplicate['date'] = date.today().isoformat()
                        duplicate['completed'] = False
                        st.session_state.cases.append(duplicate)
                        save_data()
                        st.success("Case duplicated! Edit the new case to update details.")
                        st.rerun()
                with col_d:
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
                with col_e:
                    if st.button("🗑️", key=f"delete_{case['id']}", help="Delete case"):
                        delete_case(case['id'])
                        st.rerun()
            
            # Expandable details
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

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6b7280; font-size: 0.875rem; padding: 1rem;">
    Data stored locally in case_logger_data.json. Export regularly to backup your cases.
</div>
""", unsafe_allow_html=True)
