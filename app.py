"""
Payment Reconciliation System - Professional Financial Dashboard
Simplified for Streamlit Cloud
"""

import streamlit as st
import pandas as pd
from reconciliation import ReconciliationEngine
from data_generator import generate_sample_data
from decimal import Decimal
import os

# Import plotly with fallback
try:
    import plotly.graph_objects as go
except ImportError:
    go = None

# Configure page
st.set_page_config(
    page_title="Payment Reconciliation Dashboard",
    page_icon="💰",
    layout="wide"
)

# Initialize session state
if 'platform_df' not in st.session_state:
    st.session_state.platform_df = None
if 'bank_df' not in st.session_state:
    st.session_state.bank_df = None
if 'results_df' not in st.session_state:
    st.session_state.results_df = None
if 'discrepancies' not in st.session_state:
    st.session_state.discrepancies = None
if 'reconciliation_run' not in st.session_state:
    st.session_state.reconciliation_run = False

st.title("💰 Payment Reconciliation System")

# Sidebar Navigation
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Select Page:", [
        "Dashboard",
        "Upload Data",
        "Reconciliation",
        "Discrepancies",
        "Reports"
    ], index=0)

# ==================== PAGE: DASHBOARD ====================
if page == "Dashboard":
    st.header("📊 Dashboard")
    
    # Auto-load sample data if not loaded
    if st.session_state.platform_df is None:
        with st.spinner("Loading sample data..."):
            try:
                platform_df, bank_df = generate_sample_data()
                st.session_state.platform_df = platform_df
                st.session_state.bank_df = bank_df
                st.success("✅ Sample data loaded")
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")
                st.stop()
    
    if not st.session_state.reconciliation_run:
        st.info("👉 Go to 'Reconciliation' page to run analysis.")
        
        # Quick stats
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Platform Records", len(st.session_state.platform_df))
        with col2:
            st.metric("Bank Records", len(st.session_state.bank_df))
        st.stop()
    
    # Show dashboard after reconciliation
    platform_df = st.session_state.platform_df
    bank_df = st.session_state.bank_df
    results_df = st.session_state.results_df
    discrepancies = st.session_state.discrepancies
    
    # KPI Cards
    st.subheader("Key Metrics")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    total_platform = len(platform_df)
    total_bank = len(bank_df)
    matched = len(results_df)
    unmatched = total_platform - matched
    disc_count = len(discrepancies)
    
    with col1:
        st.metric("Platform", total_platform)
    with col2:
        st.metric("Bank", total_bank)
    with col3:
        st.metric("Matched", matched)
    with col4:
        st.metric("Unmatched", unmatched)
    with col5:
        st.metric("Discrepancies", disc_count)
    with col6:
        st.metric("Success Rate", f"{(matched/total_platform*100):.1f}%")
    
    st.divider()
    
    # Test Cases
    st.subheader("🎯 Test Cases Status")
    test1 = any(d.discrepancy_type == "CROSS_MONTH_SETTLEMENT" for d in discrepancies)
    test2 = any(d.discrepancy_type == "AMOUNT_MISMATCH" for d in discrepancies)
    test3 = any("DUPLICATE" in d.discrepancy_type for d in discrepancies)
    test4 = any(d.discrepancy_type == "ORPHANED_REFUND" for d in discrepancies)
    
    col1, col2 = st.columns(2)
    with col1:
        if test1:
            st.success("✅ Cross-Month Settlement")
        else:
            st.error("❌ Cross-Month Settlement")
    with col2:
        if test2:
            st.success("✅ Rounding Variance")
        else:
            st.error("❌ Rounding Variance")
    
    col1, col2 = st.columns(2)
    with col1:
        if test3:
            st.success("✅ Duplicates Detected")
        else:
            st.error("❌ Duplicates")
    with col2:
        if test4:
            st.success("✅ Orphaned Refund")
        else:
            st.error("❌ Orphaned Refund")
    
    if sum([test1, test2, test3, test4]) == 4:
        st.balloons()

# ==================== PAGE: UPLOAD DATA ====================
elif page == "Upload Data":
    st.header("📤 Upload Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Platform CSV")
        platform_file = st.file_uploader("Upload platform data", type="csv", key="platform")
        if platform_file:
            try:
                df = pd.read_csv(platform_file)
                st.session_state.platform_df = df
                st.success(f"✅ Loaded {len(df)} records")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    with col2:
        st.subheader("Bank CSV")
        bank_file = st.file_uploader("Upload bank data", type="csv", key="bank")
        if bank_file:
            try:
                df = pd.read_csv(bank_file)
                st.session_state.bank_df = df
                st.success(f"✅ Loaded {len(df)} records")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    st.divider()
    
    if st.button("🔄 Load Sample Data", use_container_width=True):
        with st.spinner("Generating sample data..."):
            try:
                platform_df, bank_df = generate_sample_data()
                st.session_state.platform_df = platform_df
                st.session_state.bank_df = bank_df
                st.success("✅ Sample data loaded!")
            except Exception as e:
                st.error(f"Error: {str(e)}")

# ==================== PAGE: RECONCILIATION ====================
elif page == "Reconciliation":
    st.header("⚙️ Run Reconciliation")
    
    if st.session_state.platform_df is None or st.session_state.bank_df is None:
        st.warning("⚠️ Load data first")
        st.stop()
    
    st.info(f"Ready: {len(st.session_state.platform_df)} platform + {len(st.session_state.bank_df)} bank records")
    
    if st.button("🚀 Run Reconciliation", use_container_width=True):
        with st.spinner("Running reconciliation..."):
            try:
                engine = ReconciliationEngine(settlement_window_days=2, rounding_threshold=Decimal("0.01"))
                engine.load_platform_data(st.session_state.platform_df)
                engine.load_bank_data(st.session_state.bank_df)
                
                results_df, discrepancies = engine.reconcile()
                
                st.session_state.results_df = results_df
                st.session_state.discrepancies = discrepancies
                st.session_state.reconciliation_run = True
                
                st.success("✅ Complete!")
                st.rerun()
            except Exception as e:
                st.error(f"Error: {str(e)}")
    
    if st.session_state.reconciliation_run:
        st.divider()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Matched", len(st.session_state.results_df))
        with col2:
            st.metric("Discrepancies", len(st.session_state.discrepancies))
        with col3:
            st.metric("Success %", f"{(len(st.session_state.results_df)/len(st.session_state.platform_df)*100):.1f}%")

# ==================== PAGE: DISCREPANCIES ====================
elif page == "Discrepancies":
    st.header("🚨 Discrepancies")
    
    if not st.session_state.reconciliation_run:
        st.warning("⚠️ Run reconciliation first")
        st.stop()
    
    discrepancies = st.session_state.discrepancies
    
    if not discrepancies:
        st.success("✅ No discrepancies!")
        st.stop()
    
    # Filters
    col1, col2 = st.columns(2)
    with col1:
        types = sorted(list(set(d.discrepancy_type for d in discrepancies)))
        selected_type = st.multiselect("Type", types, default=types)
    with col2:
        severities = sorted(list(set(d.severity for d in discrepancies)))
        selected_severity = st.multiselect("Severity", severities, default=severities)
    
    filtered = [d for d in discrepancies if d.discrepancy_type in selected_type and d.severity in selected_severity]
    
    st.divider()
    st.subheader(f"Found: {len(filtered)}")
    
    for i, disc in enumerate(filtered, 1):
        with st.expander(f"{disc.discrepancy_type} - {', '.join(disc.transaction_ids)}", expanded=(i==1)):
            st.write(f"**Type:** {disc.discrepancy_type}")
            st.write(f"**Severity:** {disc.severity}")
            st.write(f"**Transaction IDs:** {', '.join(disc.transaction_ids)}")
            st.write(f"**Explanation:** {disc.explanation}")
            
            if disc.discrepancy_type == "CROSS_MONTH_SETTLEMENT":
                st.info("📌 Mandatory Scenario 1")
            elif "DUPLICATE" in disc.discrepancy_type:
                st.info("📌 Mandatory Scenario 3")
            elif disc.discrepancy_type == "ORPHANED_REFUND":
                st.info("📌 Mandatory Scenario 4")

# ==================== PAGE: REPORTS ====================
elif page == "Reports":
    st.header("📥 Reports")
    
    if not st.session_state.reconciliation_run:
        st.warning("⚠️ Run reconciliation first")
        st.stop()
    
    col1, col2 = st.columns(2)
    
    with col1:
        if not st.session_state.results_df.empty:
            csv = st.session_state.results_df.to_csv(index=False)
            st.download_button("📊 Matched Records", data=csv, file_name="matched.csv", mime="text/csv")
    
    with col2:
        if st.session_state.discrepancies:
            disc_data = []
            for d in st.session_state.discrepancies:
                disc_data.append({
                    'Type': d.discrepancy_type,
                    'Transaction ID': ', '.join(d.transaction_ids),
                    'Severity': d.severity,
                    'Explanation': d.explanation
                })
            disc_df = pd.DataFrame(disc_data)
            csv = disc_df.to_csv(index=False)
            st.download_button("🚨 Discrepancies", data=csv, file_name="discrepancies.csv", mime="text/csv")
    
    st.divider()
    st.subheader("Summary")
    st.text(f"""
Platform Records: {len(st.session_state.platform_df)}
Bank Records: {len(st.session_state.bank_df)}
Matched: {len(st.session_state.results_df)}
Discrepancies: {len(st.session_state.discrepancies)}
Success Rate: {(len(st.session_state.results_df)/len(st.session_state.platform_df)*100):.1f}%
    """)
