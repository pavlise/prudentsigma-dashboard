import streamlit as st
import os
from datetime import datetime
import streamlit_authenticator as stauth
import yaml

# Load config at startup
def load_config():
    with open('config.yaml') as file:
        config = yaml.safe_load(file)
    return config

# Page config
st.set_page_config(page_title="PrudentSigma Daily Market Report", layout="wide", initial_sidebar_state="collapsed")

# Initialize session state
if 'authentication_status' not in st.session_state:
    st.session_state.authentication_status = None
if 'username' not in st.session_state:
    st.session_state.username = None

# Load credentials
try:
    config = load_config()
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days'],
        config['preauthorized']
    )
    
    # Run authentication
    authenticator.login()
    
except Exception as e:
    st.error(f"Error loading authentication config: {e}")
    st.info("Please configure config.yaml with credentials")
    st.stop()

# Check if user is authenticated
if st.session_state["authentication_status"]:
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 PrudentSigma Daily Market Report Dashboard")
        st.markdown("*Smarter Strategies. Prudent Growth.*")
    with col2:
        authenticator.logout()

    # Get latest report
    reports_dir = "reports"
    latest_report = None

    if os.path.exists(reports_dir):
        # Try to find report_*.md files first (automated reports)
        report_files = [f for f in os.listdir(reports_dir) if f.startswith('report_') and f.endswith('.md')]
        
        if not report_files:
            # Fallback to DAILY_MARKET_REPORT_*.md files (manual/previous reports)
            report_files = [f for f in os.listdir(reports_dir) if f.startswith('DAILY_MARKET_REPORT_') and f.endswith('.md')]
        
        if report_files:
            # Get the latest file by modification time
            latest = max(report_files, key=lambda x: os.path.getctime(os.path.join(reports_dir, x)))
            latest_report = os.path.join(reports_dir, latest)
            report_date = latest.replace('report_', '').replace('DAILY_MARKET_REPORT_', '').replace('.md', '')
            
            st.subheader(f"Latest Report: {report_date}")

            try:
                with open(latest_report, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Display file info
                file_size = os.path.getsize(latest_report)
                st.info(f"📄 Report size: {file_size:,} bytes | Last updated: {datetime.fromtimestamp(os.path.getmtime(latest_report)).strftime('%Y-%m-%d %H:%M:%S')}")
                
                st.markdown(content)
            except Exception as e:
                st.error(f"Error loading report: {e}")

            # Manual refresh button
            if st.button("🔄 Refresh Dashboard"):
                st.rerun()
        else:
            st.warning("📭 No reports found in the reports directory yet.")
            st.info("The automated report generation will create its first report according to the schedule.")
    else:
        st.error("❌ Reports directory not found.")

elif st.session_state["authentication_status"] is False:
    st.error('Username/password is incorrect')

elif st.session_state["authentication_status"] is None:
    st.warning('Please enter your username and password')