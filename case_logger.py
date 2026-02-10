import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path

# Page config
st.set_page_config(
    page_title="Compulsion Tracker",
    page_icon="🧠",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        height: 50px;
        font-size: 18px;
        font-weight: 600;
        margin: 5px 0;
    }
    .success-button {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    .warning-button {
        background-color: #ff9800 !important;
        color: white !important;
    }
    .metric-card {
        background-color: #f9f9f9;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
    }
    .metric-value {
        font-size: 36px;
        font-weight: 700;
        color: #4CAF50;
    }
    .metric-label {
        font-size: 14px;
        color: #666;
        margin-top: 5px;
    }
    div[data-testid="stNumberInput"] input {
        font-size: 20px;
        text-align: center;
        height: 50px;
    }
    </style>
""", unsafe_allow_html=True)

# Data file path
DATA_FILE = Path("compulsion_data.json")

# Initialize session state
if 'entries' not in st.session_state:
    if DATA_FILE.exists():
        with open(DATA_FILE, 'r') as f:
            st.session_state.entries = json.load(f)
    else:
        st.session_state.entries = []

def save_data():
    """Save entries to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(st.session_state.entries, f, indent=2)

def add_entry(trigger, urge, resisted, anxiety, notes=""):
    """Add new entry to the tracker"""
    entry = {
        'timestamp': datetime.now().isoformat(),
        'trigger': trigger,
        'urge': urge,
        'resisted': resisted,
        'anxiety': anxiety,
        'notes': notes
    }
    st.session_state.entries.insert(0, entry)
    save_data()

def get_stats():
    """Calculate statistics from entries"""
    if not st.session_state.entries:
        return None
    
    df = pd.DataFrame(st.session_state.entries)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Overall stats
    total = len(df)
    resisted_count = df['resisted'].sum()
    resist_rate = (resisted_count / total * 100) if total > 0 else 0
    
    # Last 7 days
    seven_days_ago = datetime.now() - timedelta(days=7)
    recent = df[df['timestamp'] > seven_days_ago]
    recent_total = len(recent)
    recent_resisted = recent['resisted'].sum() if recent_total > 0 else 0
    recent_rate = (recent_resisted / recent_total * 100) if recent_total > 0 else 0
    
    # Averages
    avg_urge = df['urge'].mean()
    avg_anxiety = df['anxiety'].mean()
    
    # Anxiety reduction when resisted
    resisted_entries = df[df['resisted'] == True]
    avg_reduction = (resisted_entries['urge'] - resisted_entries['anxiety']).mean() if len(resisted_entries) > 0 else 0
    
    return {
        'total': total,
        'resist_rate': resist_rate,
        'recent_rate': recent_rate,
        'recent_total': recent_total,
        'avg_urge': avg_urge,
        'avg_anxiety': avg_anxiety,
        'avg_reduction': avg_reduction,
        'df': df
    }

# Main app
st.title("🧠 Compulsion Tracker")

# Tab selection
tab1, tab2, tab3 = st.tabs(["📝 Log Entry", "📊 Stats", "📋 History"])

# TAB 1: Log Entry
with tab1:
    st.markdown("### Quick Log")
    
    with st.form("entry_form", clear_on_submit=True):
        trigger = st.text_input(
            "What triggered it?",
            placeholder="e.g., Uncertain about drug dose",
            help="Brief description of what happened"
        )
        
        st.markdown("**Initial urge intensity**")
        urge = st.slider("", 0, 10, 5, key="urge_slider", label_visibility="collapsed")
        
        st.markdown("**Did you resist the compulsion?**")
        col1, col2 = st.columns(2)
        with col1:
            resist_yes = st.form_submit_button("✓ Yes", use_container_width=True)
        with col2:
            resist_no = st.form_submit_button("✗ No", use_container_width=True)
        
        resisted = None
        if resist_yes:
            resisted = True
        elif resist_no:
            resisted = False
        
        st.markdown("**Anxiety after 10 minutes**")
        anxiety = st.slider("", 0, 10, 5, key="anxiety_slider", label_visibility="collapsed")
        
        notes = st.text_area(
            "Notes (optional)",
            placeholder="What helped? What was difficult?",
            height=100
        )
        
        submitted = st.form_submit_button("💾 Save Entry", use_container_width=True, type="primary")
        
        if submitted or resisted is not None:
            if not trigger:
                st.error("Please describe what triggered it")
            elif resisted is None:
                st.error("Please indicate if you resisted")
            else:
                add_entry(trigger, urge, resisted, anxiety, notes)
                st.success("✓ Entry saved!")
                st.balloons()

# TAB 2: Stats
with tab2:
    stats = get_stats()
    
    if stats is None:
        st.info("No entries yet. Log your first observation!")
    else:
        st.markdown("### Progress Overview")
        
        # Key metrics in columns
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{stats['resist_rate']:.0f}%</div>
                    <div class="metric-label">Overall Success Rate</div>
                    <div class="metric-label" style="color: #999; font-size: 12px;">
                        {stats['total']} total entries
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value">{stats['recent_rate']:.0f}%</div>
                    <div class="metric-label">Last 7 Days</div>
                    <div class="metric-label" style="color: #999; font-size: 12px;">
                        {stats['recent_total']} entries
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #2196F3;">{stats['avg_urge']:.1f}</div>
                    <div class="metric-label">Avg Initial Urge</div>
                </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
                <div class="metric-card">
                    <div class="metric-value" style="color: #2196F3;">{stats['avg_anxiety']:.1f}</div>
                    <div class="metric-label">Avg Anxiety After</div>
                </div>
            """, unsafe_allow_html=True)
        
        if stats['avg_reduction'] > 0:
            st.markdown(f"""
                <div class="metric-card" style="background-color: #e8f5e9;">
                    <div class="metric-value" style="color: #2e7d32;">-{stats['avg_reduction']:.1f}</div>
                    <div class="metric-label">Avg Anxiety Reduction (when resisted)</div>
                </div>
            """, unsafe_allow_html=True)
        
        # Charts
        st.markdown("### Trends")
        
        df = stats['df'].copy()
        df['date'] = df['timestamp'].dt.date
        
        # Success rate over time (7-day rolling)
        if len(df) > 7:
            df_sorted = df.sort_values('timestamp')
            df_sorted['resist_rate_7d'] = df_sorted['resisted'].rolling(window=7, min_periods=1).mean() * 100
            
            fig_rate = px.line(
                df_sorted,
                x='timestamp',
                y='resist_rate_7d',
                title='Success Rate (7-day rolling average)',
                labels={'resist_rate_7d': 'Success Rate (%)', 'timestamp': 'Date'}
            )
            fig_rate.update_traces(line_color='#4CAF50', line_width=3)
            fig_rate.update_layout(
                height=300,
                showlegend=False,
                hovermode='x unified'
            )
            st.plotly_chart(fig_rate, use_container_width=True)
        
        # Urge vs Anxiety comparison
        fig_compare = go.Figure()
        fig_compare.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['urge'],
            name='Initial Urge',
            mode='markers',
            marker=dict(size=8, color='#ff9800', opacity=0.6)
        ))
        fig_compare.add_trace(go.Scatter(
            x=df['timestamp'],
            y=df['anxiety'],
            name='Anxiety After',
            mode='markers',
            marker=dict(size=8, color='#2196F3', opacity=0.6)
        ))
        fig_compare.update_layout(
            title='Urge vs Anxiety Over Time',
            height=300,
            hovermode='x unified',
            yaxis_title='Intensity (0-10)'
        )
        st.plotly_chart(fig_compare, use_container_width=True)
        
        # Daily summary
        daily_stats = df.groupby('date').agg({
            'resisted': ['count', 'sum']
        }).reset_index()
        daily_stats.columns = ['date', 'total', 'resisted']
        daily_stats['rate'] = (daily_stats['resisted'] / daily_stats['total'] * 100)
        
        fig_daily = px.bar(
            daily_stats.tail(14),
            x='date',
            y='total',
            color='rate',
            title='Daily Entry Count (Last 14 Days)',
            labels={'total': 'Entries', 'rate': 'Success %', 'date': 'Date'},
            color_continuous_scale='RdYlGn'
        )
        fig_daily.update_layout(height=300)
        st.plotly_chart(fig_daily, use_container_width=True)

# TAB 3: History
with tab3:
    if not st.session_state.entries:
        st.info("No entries yet. Log your first observation!")
    else:
        st.markdown(f"### Recent Entries ({len(st.session_state.entries)} total)")
        
        # Filter options
        col1, col2 = st.columns([2, 1])
        with col1:
            filter_days = st.selectbox(
                "Show entries from:",
                ["All time", "Last 7 days", "Last 30 days", "Today"],
                key="filter_days"
            )
        with col2:
            filter_resisted = st.selectbox(
                "Filter by:",
                ["All", "Resisted", "Not resisted"],
                key="filter_resisted"
            )
        
        # Apply filters
        filtered_entries = st.session_state.entries.copy()
        
        if filter_days != "All time":
            now = datetime.now()
            if filter_days == "Last 7 days":
                cutoff = now - timedelta(days=7)
            elif filter_days == "Last 30 days":
                cutoff = now - timedelta(days=30)
            else:  # Today
                cutoff = now.replace(hour=0, minute=0, second=0, microsecond=0)
            
            filtered_entries = [e for e in filtered_entries if datetime.fromisoformat(e['timestamp']) > cutoff]
        
        if filter_resisted != "All":
            target = filter_resisted == "Resisted"
            filtered_entries = [e for e in filtered_entries if e['resisted'] == target]
        
        # Display entries
        if not filtered_entries:
            st.info("No entries match your filters")
        else:
            for entry in filtered_entries:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                formatted_time = timestamp.strftime("%d %b, %H:%M")
                
                # Color coding
                if entry['resisted']:
                    border_color = "#4CAF50"
                    badge_color = "#e8f5e9"
                    badge_text_color = "#2e7d32"
                    badge_label = "Resisted ✓"
                else:
                    border_color = "#ff9800"
                    badge_color = "#fff3e0"
                    badge_text_color = "#e65100"
                    badge_label = "Gave in"
                
                reduction = entry['urge'] - entry['anxiety']
                
                st.markdown(f"""
                    <div style="
                        border-left: 4px solid {border_color};
                        padding: 16px;
                        margin: 12px 0;
                        background: #f9f9f9;
                        border-radius: 4px;
                    ">
                        <div style="
                            display: flex;
                            justify-content: space-between;
                            align-items: center;
                            margin-bottom: 12px;
                        ">
                            <span style="color: #666; font-size: 14px;">{formatted_time}</span>
                            <span style="
                                padding: 4px 12px;
                                border-radius: 12px;
                                font-size: 12px;
                                font-weight: 600;
                                background: {badge_color};
                                color: {badge_text_color};
                            ">{badge_label}</span>
                        </div>
                        <div style="font-weight: 500; margin-bottom: 8px;">{entry['trigger']}</div>
                        <div style="font-size: 14px; color: #666;">
                            <strong>Initial urge:</strong> {entry['urge']}/10 &nbsp;&nbsp;
                            <strong>Anxiety after:</strong> {entry['anxiety']}/10
                            {f' &nbsp;&nbsp; <strong>Reduction:</strong> {reduction}' if entry['resisted'] and reduction > 0 else ''}
                        </div>
                        {f'<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid #e0e0e0; font-size: 14px; color: #555; font-style: italic;">{entry["notes"]}</div>' if entry['notes'] else ''}
                    </div>
                """, unsafe_allow_html=True)
        
        # Clear data option
        st.markdown("---")
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.checkbox("I'm sure I want to delete all entries"):
                st.session_state.entries = []
                save_data()
                st.success("All data cleared")
                st.rerun()

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #999; font-size: 12px; padding: 20px;">
        Data stored locally in compulsion_data.json
    </div>
""", unsafe_allow_html=True)
