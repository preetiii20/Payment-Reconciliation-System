import streamlit as st
import pandas as pd
from reconciliation import ReconciliationEngine
from data_generator import generate_sample_data
from decimal import Decimal
import os

st.set_page_config(page_title="Payment Reconciliation", layout="wide")
st.title("💰 Payment Reconciliation System")

# Initialize session state
for key in ['platform_df', 'bank_df', 'results_df', 'discrepancies', 'reconciliation_run']:
    if key not in st.session_state:
        st.session_state[key] = None if key != 'reconciliation_run' else False

# Sidebar
with st.sidebar:
    page = st.radio("Select:", ["Dashboard", "Upload", "Reconciliation", "Discrepancies", "Reports"])

# Auto-load sample data on first visit
if st.session_state.platform_df is None:
    try:
        platform_df, bank_df = generate_sample_data()
        st.session_state.platform_df = platform_df
        st.session_state.bank_df = bank_df
    except Exception as e:
        st.error(f"Error loading data: {e}")

# PAGE: DASHBOARD
if page == "Dashboard":
    st.header("📊 Dashboard")
    
    if not st.session_state.reconciliation_run:
        st.info("Run reconciliation to see results")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Platform", len(st.session_state.platform_df))
        with col2:
            st.metric("Bank", len(st.session_state.bank_df))
    else:
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        with col1:
            st.metric("Platform", len(st.session_state.platform_df))
        with col2:
            st.metric("Bank", len(st.session_state.bank_df))
        with col3:
            st.metric("Matched", len(st.session_state.results_df))
        with col4:
            st.metric("Unmatched", len(st.session_state.platform_df) - len(st.session_state.results_df))
        with col5:
            st.metric("Discrepancies", len(st.session_state.discrepancies))
        with col6:
            pct = (len(st.session_state.results_df) / len(st.session_state.platform_df) * 100)
            st.metric("Success %", f"{pct:.1f}%")
        
        st.divider()
        st.subheader("Test Cases")
        
        disc = st.session_state.discrepancies
        t1 = any(d.discrepancy_type == "CROSS_MONTH_SETTLEMENT" for d in disc)
        t2 = any(d.discrepancy_type == "AMOUNT_MISMATCH" for d in disc)
        t3 = any("DUPLICATE" in d.discrepancy_type for d in disc)
        t4 = any(d.discrepancy_type == "ORPHANED_REFUND" for d in disc)
        
        col1, col2 = st.columns(2)
        with col1:
            st.success("✅ Cross-Month") if t1 else st.error("❌ Cross-Month")
        with col2:
            st.success("✅ Rounding") if t2 else st.error("❌ Rounding")
        
        col1, col2 = st.columns(2)
        with col1:
            st.success("✅ Duplicates") if t3 else st.error("❌ Duplicates")
        with col2:
            st.success("✅ Orphaned") if t4 else st.error("❌ Orphaned")

# PAGE: UPLOAD
elif page == "Upload":
    st.header("📤 Upload Data")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Platform")
        f = st.file_uploader("Platform CSV", type="csv", key="p")
        if f:
            st.session_state.platform_df = pd.read_csv(f)
            st.success("✅ Loaded")
    
    with col2:
        st.subheader("Bank")
        f = st.file_uploader("Bank CSV", type="csv", key="b")
        if f:
            st.session_state.bank_df = pd.read_csv(f)
            st.success("✅ Loaded")
    
    st.divider()
    if st.button("Load Sample Data", use_container_width=True):
        try:
            p, b = generate_sample_data()
            st.session_state.platform_df = p
            st.session_state.bank_df = b
            st.success("✅ Sample data loaded")
        except Exception as e:
            st.error(f"Error: {e}")

# PAGE: RECONCILIATION
elif page == "Reconciliation":
    st.header("⚙️ Reconciliation")
    
    if st.session_state.platform_df is None:
        st.warning("Load data first")
    else:
        st.info(f"Ready: {len(st.session_state.platform_df)} + {len(st.session_state.bank_df)} records")
        
        if st.button("Run Reconciliation", use_container_width=True):
            with st.spinner("Processing..."):
                try:
                    engine = ReconciliationEngine(settlement_window_days=2, rounding_threshold=Decimal("0.01"))
                    engine.load_platform_data(st.session_state.platform_df)
                    engine.load_bank_data(st.session_state.bank_df)
                    
                    results, discs = engine.reconcile()
                    st.session_state.results_df = results
                    st.session_state.discrepancies = discs
                    st.session_state.reconciliation_run = True
                    
                    st.success("✅ Complete")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

# PAGE: DISCREPANCIES
elif page == "Discrepancies":
    st.header("🚨 Discrepancies")
    
    if not st.session_state.reconciliation_run:
        st.warning("Run reconciliation first")
    else:
        discs = st.session_state.discrepancies
        if not discs:
            st.success("✅ No discrepancies")
        else:
            st.subheader(f"Found: {len(discs)}")
            for i, d in enumerate(discs, 1):
                with st.expander(f"{d.discrepancy_type} - {d.transaction_ids[0]}", expanded=(i==1)):
                    st.write(f"**Type:** {d.discrepancy_type}")
                    st.write(f"**Severity:** {d.severity}")
                    st.write(f"**Explanation:** {d.explanation}")

# PAGE: REPORTS
elif page == "Reports":
    st.header("📥 Reports")
    
    if not st.session_state.reconciliation_run:
        st.warning("Run reconciliation first")
    else:
        col1, col2 = st.columns(2)
        with col1:
            if len(st.session_state.results_df) > 0:
                csv = st.session_state.results_df.to_csv(index=False)
                st.download_button("Matched Records", csv, "matched.csv", "text/csv")
        
        with col2:
            if len(st.session_state.discrepancies) > 0:
                data = [{
                    'Type': d.discrepancy_type,
                    'ID': d.transaction_ids[0],
                    'Severity': d.severity
                } for d in st.session_state.discrepancies]
                csv = pd.DataFrame(data).to_csv(index=False)
                st.download_button("Discrepancies", csv, "discrepancies.csv", "text/csv")
