import streamlit as st
import pandas as pd
from reconciliation import ReconciliationEngine
from data_generator import generate_sample_data
from decimal import Decimal
import os

st.set_page_config(page_title="Payment Reconciliation", layout="wide")

# Custom CSS
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    .main {
        padding: 2rem;
    }
</style>
""", unsafe_allow_html=True)

st.title("💰 Payment Reconciliation System")

# Initialize session state
for key in ['platform_df', 'bank_df', 'results_df', 'discrepancies', 'reconciliation_run']:
    if key not in st.session_state:
        st.session_state[key] = None if key != 'reconciliation_run' else False

# Sidebar
with st.sidebar:
    st.header("📋 Navigation")
    page = st.radio("Select Page:", ["Dashboard", "Upload Data", "Reconciliation", "Discrepancies", "Reports"], label_visibility="collapsed")

# Auto-load sample data on first visit
if st.session_state.platform_df is None:
    with st.spinner("Loading sample data..."):
        try:
            platform_df, bank_df = generate_sample_data()
            st.session_state.platform_df = platform_df
            st.session_state.bank_df = bank_df
        except Exception as e:
            st.error(f"Error loading data: {e}")

# ========== DASHBOARD ==========
if page == "Dashboard":
    st.header("📊 Dashboard")
    
    if not st.session_state.reconciliation_run:
        st.info("👉 Go to 'Reconciliation' page to run analysis")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Platform Records", len(st.session_state.platform_df) if st.session_state.platform_df is not None else 0)
        with col2:
            st.metric("Bank Records", len(st.session_state.bank_df) if st.session_state.bank_df is not None else 0)
    else:
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        platform_len = len(st.session_state.platform_df)
        bank_len = len(st.session_state.bank_df)
        results_len = len(st.session_state.results_df)
        unmatched = platform_len - results_len
        disc_len = len(st.session_state.discrepancies)
        success_rate = (results_len / platform_len * 100) if platform_len > 0 else 0
        
        with col1:
            st.metric("Platform", platform_len)
        with col2:
            st.metric("Bank", bank_len)
        with col3:
            st.metric("Matched", results_len)
        with col4:
            st.metric("Unmatched", unmatched)
        with col5:
            st.metric("Discrepancies", disc_len)
        with col6:
            st.metric("Success %", f"{success_rate:.1f}%")
        
        st.divider()
        st.subheader("🎯 Test Cases")
        
        disc = st.session_state.discrepancies
        t1 = any(d.discrepancy_type == "CROSS_MONTH_SETTLEMENT" for d in disc)
        t2 = any(d.discrepancy_type == "AMOUNT_MISMATCH" for d in disc)
        t3 = any("DUPLICATE" in d.discrepancy_type for d in disc)
        t4 = any(d.discrepancy_type == "ORPHANED_REFUND" for d in disc)
        
        col1, col2 = st.columns(2)
        with col1:
            if t1:
                st.success("✅ Cross-Month Settlement")
            else:
                st.error("❌ Cross-Month Settlement")
        with col2:
            if t2:
                st.success("✅ Rounding Variance")
            else:
                st.error("❌ Rounding Variance")
        
        col1, col2 = st.columns(2)
        with col1:
            if t3:
                st.success("✅ Duplicate Detection")
            else:
                st.error("❌ Duplicate Detection")
        with col2:
            if t4:
                st.success("✅ Orphaned Refund")
            else:
                st.error("❌ Orphaned Refund")
        
        if sum([t1, t2, t3, t4]) == 4:
            st.balloons()

# ========== UPLOAD DATA ==========
elif page == "Upload Data":
    st.header("📤 Upload Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Platform CSV")
        uploaded_platform = st.file_uploader("Upload Payment Platform CSV", type="csv", key="platform_upload")
        if uploaded_platform:
            try:
                df = pd.read_csv(uploaded_platform)
                st.session_state.platform_df = df
                st.success(f"✅ Loaded {len(df)} records")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        st.subheader("Bank Settlement CSV")
        uploaded_bank = st.file_uploader("Upload Bank Settlement CSV", type="csv", key="bank_upload")
        if uploaded_bank:
            try:
                df = pd.read_csv(uploaded_bank)
                st.session_state.bank_df = df
                st.success(f"✅ Loaded {len(df)} records")
            except Exception as e:
                st.error(f"Error: {e}")

# ========== RECONCILIATION ==========
elif page == "Reconciliation":
    st.header("⚙️ Run Reconciliation")
    
    if st.session_state.platform_df is None or st.session_state.bank_df is None:
        st.error("❌ Data not loaded")
    else:
        st.info(f"✅ Ready: {len(st.session_state.platform_df)} platform + {len(st.session_state.bank_df)} bank records")
        
        if st.button("🚀 Run Reconciliation", use_container_width=True, type="primary"):
            with st.spinner("Processing reconciliation..."):
                try:
                    engine = ReconciliationEngine(settlement_window_days=2, rounding_threshold=Decimal("0.01"))
                    engine.load_platform_data(st.session_state.platform_df)
                    engine.load_bank_data(st.session_state.bank_df)
                    
                    results, discs = engine.reconcile()
                    st.session_state.results_df = results
                    st.session_state.discrepancies = discs
                    st.session_state.reconciliation_run = True
                    
                    st.success("✅ Reconciliation Complete!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        
        if st.session_state.reconciliation_run:
            st.divider()
            st.subheader("Results")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Matched", len(st.session_state.results_df))
            with col2:
                st.metric("Discrepancies", len(st.session_state.discrepancies))
            with col3:
                pct = (len(st.session_state.results_df) / len(st.session_state.platform_df) * 100) if len(st.session_state.platform_df) > 0 else 0
                st.metric("Success Rate", f"{pct:.1f}%")

# ========== DISCREPANCIES ==========
elif page == "Discrepancies":
    st.header("🚨 Discrepancies")
    
    if not st.session_state.reconciliation_run:
        st.warning("⚠️ Run reconciliation first")
    else:
        discs = st.session_state.discrepancies
        if not discs:
            st.success("✅ No discrepancies found!")
        else:
            st.subheader(f"Found: {len(discs)} issues")
            
            # Filters
            col1, col2 = st.columns(2)
            with col1:
                types = sorted(list(set(d.discrepancy_type for d in discs)))
                selected_types = st.multiselect("Filter by Type:", types, default=types)
            with col2:
                severities = sorted(list(set(d.severity for d in discs)))
                selected_severities = st.multiselect("Filter by Severity:", severities, default=severities)
            
            filtered = [d for d in discs if d.discrepancy_type in selected_types and d.severity in selected_severities]
            
            st.divider()
            
            for i, d in enumerate(filtered, 1):
                with st.expander(f"**{d.discrepancy_type}** - {d.transaction_ids[0] if d.transaction_ids else 'N/A'}", expanded=(i<=2)):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Type:** {d.discrepancy_type}")
                        st.write(f"**Severity:** {d.severity}")
                    with col2:
                        st.write(f"**Transaction ID(s):** {', '.join(d.transaction_ids)}")
                    
                    st.write(f"**Explanation:** {d.explanation}")
                    
                    # Mandatory scenario indicators
                    if d.discrepancy_type == "CROSS_MONTH_SETTLEMENT":
                        st.info("📌 Mandatory Scenario 1: Cross-Month Settlement")
                    elif d.discrepancy_type == "AMOUNT_MISMATCH":
                        st.info("📌 Mandatory Scenario 2: Rounding Variance")
                    elif "DUPLICATE" in d.discrepancy_type:
                        st.info("📌 Mandatory Scenario 3: Duplicate Detection")
                    elif d.discrepancy_type == "ORPHANED_REFUND":
                        st.info("📌 Mandatory Scenario 4: Orphaned Refund")

# ========== REPORTS ==========
elif page == "Reports":
    st.header("📥 Reports & Downloads")
    
    if not st.session_state.reconciliation_run:
        st.warning("⚠️ Run reconciliation first")
    else:
        st.subheader("Download Results")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if len(st.session_state.results_df) > 0:
                csv = st.session_state.results_df.to_csv(index=False)
                st.download_button(
                    label="📊 Matched Records",
                    data=csv,
                    file_name="matched_records.csv",
                    mime="text/csv"
                )
            else:
                st.info("No matched records")
        
        with col2:
            if len(st.session_state.discrepancies) > 0:
                data = []
                for d in st.session_state.discrepancies:
                    data.append({
                        'Type': d.discrepancy_type,
                        'Transaction ID': ', '.join(d.transaction_ids),
                        'Severity': d.severity,
                        'Explanation': d.explanation
                    })
                df = pd.DataFrame(data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="🚨 Discrepancies",
                    data=csv,
                    file_name="discrepancies.csv",
                    mime="text/csv"
                )
            else:
                st.info("No discrepancies")
        
        with col3:
            if st.session_state.platform_df is not None:
                csv = st.session_state.platform_df.to_csv(index=False)
                st.download_button(
                    label="💳 Platform Data",
                    data=csv,
                    file_name="platform_data.csv",
                    mime="text/csv"
                )
        
        st.divider()
        st.subheader("Summary Report")
        
        summary = f"""
### Reconciliation Summary

- **Platform Transactions:** {len(st.session_state.platform_df)}
- **Bank Records:** {len(st.session_state.bank_df)}
- **Matched:** {len(st.session_state.results_df)}
- **Discrepancies:** {len(st.session_state.discrepancies)}
- **Success Rate:** {(len(st.session_state.results_df) / len(st.session_state.platform_df) * 100):.1f}%

### Discrepancy Breakdown
"""
        
        disc_types = {}
        for d in st.session_state.discrepancies:
            disc_types[d.discrepancy_type] = disc_types.get(d.discrepancy_type, 0) + 1
        
        for dtype, count in sorted(disc_types.items()):
            summary += f"\n- **{dtype}:** {count}"
        
        st.markdown(summary)
