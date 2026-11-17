"""
Payment Reconciliation System - Professional Financial Dashboard
"""

import streamlit as st
import pandas as pd
from reconciliation import ReconciliationEngine
from data_generator import generate_sample_data, export_sample_data
from decimal import Decimal
import os

try:
    import plotly.graph_objects as go
    import plotly.express as px
except ImportError:
    st.error("Plotly not installed. Reinstalling...")
    import subprocess
    subprocess.run(["pip", "install", "plotly", "kaleido"], check=True)
    import plotly.graph_objects as go
    import plotly.express as px

# Configure page
st.set_page_config(
    page_title="Payment Reconciliation Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional theme
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
    .success-card {
        background-color: #d4edda;
        border-left: 4px solid #28a745;
    }
    .error-card {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

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

# Sidebar Navigation
with st.sidebar:
    st.title("💰 Navigation")
    page = st.radio("Select Page:", [
        "Dashboard",
        "Upload Data",
        "Reconciliation",
        "Discrepancies",
        "Reports"
    ], index=0)

# ==================== PAGE: DASHBOARD ====================
if page == "Dashboard":
    st.title("📊 Dashboard")
    
    if not st.session_state.reconciliation_run:
        st.info("👉 Load data and run reconciliation to see dashboard metrics.")
        st.stop()
    
    platform_df = st.session_state.platform_df
    bank_df = st.session_state.bank_df
    results_df = st.session_state.results_df
    discrepancies = st.session_state.discrepancies
    
    # KPI Cards
    st.subheader("Key Performance Indicators")
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    total_platform = len(platform_df)
    total_bank = len(bank_df)
    matched = len(results_df)
    unmatched = total_platform - matched
    disc_count = len(discrepancies)
    
    # Calculate total variance
    total_variance = Decimal(0)
    for disc in discrepancies:
        if disc.amounts:
            total_variance += sum(Decimal(str(a)) for a in disc.amounts)
    
    with col1:
        st.metric("Platform Txns", total_platform, delta=None)
    with col2:
        st.metric("Bank Records", total_bank, delta=None)
    with col3:
        st.metric("Matched", matched, delta=f"{(matched/total_platform*100):.1f}%")
    with col4:
        st.metric("Unmatched", unmatched)
    with col5:
        st.metric("Discrepancies", disc_count)
    with col6:
        st.metric("Variance", f"₹{total_variance}")
    
    st.divider()
    
    # Reconciliation Status Chart
    st.subheader("Reconciliation Status")
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart: Matched vs Unmatched
        status_data = {
            'Status': ['Matched', 'Unmatched'],
            'Count': [matched, unmatched]
        }
        fig_status = go.Figure(data=[go.Pie(
            labels=status_data['Status'],
            values=status_data['Count'],
            marker=dict(colors=['#28a745', '#dc3545']),
            hole=0.3
        )])
        fig_status.update_layout(title="Match Status", height=400)
        st.plotly_chart(fig_status, use_container_width=True)
    
    with col2:
        # Bar chart: Discrepancy types
        disc_types = {}
        for disc in discrepancies:
            disc_types[disc.discrepancy_type] = disc_types.get(disc.discrepancy_type, 0) + 1
        
        if disc_types:
            fig_disc = go.Figure(data=[go.Bar(
                x=list(disc_types.keys()),
                y=list(disc_types.values()),
                marker_color='#ff7f0e'
            )])
            fig_disc.update_layout(title="Discrepancies by Type", xaxis_title="Type", yaxis_title="Count", height=400)
            st.plotly_chart(fig_disc, use_container_width=True)
        else:
            st.info("No discrepancies found!")
    
    st.divider()
    
    # Test Cases Status
    st.subheader("🎯 Test Cases Status")
    test1 = any(d.discrepancy_type == "CROSS_MONTH_SETTLEMENT" for d in discrepancies)
    test2 = any(d.discrepancy_type == "AMOUNT_MISMATCH" for d in discrepancies)
    test3 = any("DUPLICATE" in d.discrepancy_type for d in discrepancies)
    test4 = any(d.discrepancy_type == "ORPHANED_REFUND" for d in discrepancies)
    
    col1, col2 = st.columns(2)
    with col1:
        if test1:
            st.success("✅ Cross-Month Settlement Detected")
        else:
            st.error("❌ Cross-Month Settlement Not Found")
    with col2:
        if test2:
            st.success("✅ Rounding Variance Detected")
        else:
            st.error("❌ Rounding Variance Not Found")
    
    col1, col2 = st.columns(2)
    with col1:
        if test3:
            st.success("✅ Duplicates Detected")
        else:
            st.error("❌ Duplicates Not Found")
    with col2:
        if test4:
            st.success("✅ Orphaned Refund Detected")
        else:
            st.error("❌ Orphaned Refund Not Found")
    
    if sum([test1, test2, test3, test4]) == 4:
        st.balloons()
        st.success("🎉 ALL TEST CASES PASSED!")

# ==================== PAGE: UPLOAD DATA ====================
elif page == "Upload Data":
    st.title("📤 Upload Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Payment Platform CSV")
        platform_file = st.file_uploader("Upload platform transactions", type="csv", key="platform_upload")
        
        if platform_file:
            try:
                platform_df = pd.read_csv(platform_file)
                st.session_state.platform_df = platform_df
                st.success(f"✅ Loaded {len(platform_df)} records")
                
                # Validate columns
                required_cols = ['transaction_id', 'transaction_date', 'amount', 'transaction_type', 'status', 'currency']
                missing = [col for col in required_cols if col not in platform_df.columns]
                if missing:
                    st.error(f"❌ Missing columns: {missing}")
                else:
                    st.info("✅ All required columns present")
                
                # Preview
                with st.expander("Preview Data"):
                    st.dataframe(platform_df.head(10), use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    with col2:
        st.subheader("Bank Settlement CSV")
        bank_file = st.file_uploader("Upload bank settlements", type="csv", key="bank_upload")
        
        if bank_file:
            try:
                bank_df = pd.read_csv(bank_file)
                st.session_state.bank_df = bank_df
                st.success(f"✅ Loaded {len(bank_df)} records")
                
                # Validate columns
                required_cols = ['settlement_id', 'transaction_id', 'settlement_date', 'amount', 'transaction_type', 'status', 'currency']
                missing = [col for col in required_cols if col not in bank_df.columns]
                if missing:
                    st.error(f"❌ Missing columns: {missing}")
                else:
                    st.info("✅ All required columns present")
                
                # Preview
                with st.expander("Preview Data"):
                    st.dataframe(bank_df.head(10), use_container_width=True)
            except Exception as e:
                st.error(f"❌ Error reading file: {str(e)}")
    
    st.divider()
    
    # Load Sample Data Button
    st.subheader("Load Sample Data")
    if st.button("🔄 Generate & Load Sample Data", use_container_width=True):
        with st.spinner("Generating sample data..."):
            try:
                platform_df, bank_df = generate_sample_data()
                export_sample_data(platform_df, bank_df, output_dir="data")
                st.session_state.platform_df = platform_df
                st.session_state.bank_df = bank_df
                st.success("✅ Sample data generated and loaded!")
            except Exception as e:
                st.error(f"❌ Error generating sample data: {str(e)}")

# ==================== PAGE: RECONCILIATION ====================
elif page == "Reconciliation":
    st.title("⚙️ Run Reconciliation")
    
    if st.session_state.platform_df is None or st.session_state.bank_df is None:
        st.warning("⚠️ Please load both platform and bank data first.")
        st.stop()
    
    st.info(f"Ready to reconcile: {len(st.session_state.platform_df)} platform + {len(st.session_state.bank_df)} bank records")
    
    # Run Reconciliation Button
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
                
                st.success("✅ Reconciliation completed!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Reconciliation error: {str(e)}")
    
    # Display results if available
    if st.session_state.reconciliation_run:
        st.divider()
        st.subheader("Results Summary")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Matched", len(st.session_state.results_df))
        with col2:
            st.metric("Discrepancies", len(st.session_state.discrepancies))
        with col3:
            st.metric("Success Rate", f"{(len(st.session_state.results_df)/len(st.session_state.platform_df)*100):.1f}%")
        
        st.divider()
        
        st.subheader("Matched Records")
        if not st.session_state.results_df.empty:
            st.dataframe(st.session_state.results_df, use_container_width=True)
        else:
            st.info("No matched records")

# ==================== PAGE: DISCREPANCIES ====================
elif page == "Discrepancies":
    st.title("🚨 Discrepancies")
    
    if not st.session_state.reconciliation_run:
        st.warning("⚠️ Run reconciliation first to see discrepancies.")
        st.stop()
    
    discrepancies = st.session_state.discrepancies
    
    if not discrepancies:
        st.success("✅ No discrepancies found!")
        st.stop()
    
    # Filters
    st.subheader("Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        disc_types = sorted(list(set(d.discrepancy_type for d in discrepancies)))
        selected_type = st.multiselect("Discrepancy Type", disc_types, default=disc_types)
    
    with col2:
        severities = sorted(list(set(d.severity for d in discrepancies)))
        selected_severity = st.multiselect("Severity", severities, default=severities)
    
    # Filter discrepancies
    filtered = [d for d in discrepancies if d.discrepancy_type in selected_type and d.severity in selected_severity]
    
    st.divider()
    st.subheader(f"Discrepancies ({len(filtered)} found)")
    
    # Display discrepancies
    for i, disc in enumerate(filtered, 1):
        with st.expander(f"{disc.discrepancy_type} - {', '.join(disc.transaction_ids)}", expanded=(i==1)):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Type:** {disc.discrepancy_type}")
                st.write(f"**Severity:** {disc.severity}")
                st.write(f"**Transaction IDs:** {', '.join(disc.transaction_ids)}")
            with col2:
                st.write(f"**Amounts:** {', '.join(str(a) for a in disc.amounts)}")
                st.write(f"**Datasets:** {', '.join(disc.affected_datasets)}")
            
            st.write(f"**Explanation:** {disc.explanation}")
            
            # Highlight mandatory scenarios
            if disc.discrepancy_type == "CROSS_MONTH_SETTLEMENT":
                st.info("📌 Mandatory Scenario 1: Cross-Month Settlement")
            elif disc.discrepancy_type == "AMOUNT_MISMATCH" and "TXN20241110" in str(disc.transaction_ids):
                st.info("📌 Mandatory Scenario 2: Rounding Variance")
            elif "DUPLICATE" in disc.discrepancy_type:
                st.info("📌 Mandatory Scenario 3: Duplicate Detection")
            elif disc.discrepancy_type == "ORPHANED_REFUND":
                st.info("📌 Mandatory Scenario 4: Orphaned Refund")

# ==================== PAGE: REPORTS ====================
elif page == "Reports":
    st.title("📥 Reports & Downloads")
    
    if not st.session_state.reconciliation_run:
        st.warning("⚠️ Run reconciliation first to generate reports.")
        st.stop()
    
    st.subheader("Export Results")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download matched records
        if not st.session_state.results_df.empty:
            csv = st.session_state.results_df.to_csv(index=False)
            st.download_button(
                label="📊 Matched Records (CSV)",
                data=csv,
                file_name="reconciliation_matched.csv",
                mime="text/csv"
            )
        else:
            st.info("No matched records to download")
    
    with col2:
        # Download discrepancies
        if st.session_state.discrepancies:
            disc_data = []
            for d in st.session_state.discrepancies:
                disc_data.append({
                    'Type': d.discrepancy_type,
                    'Transaction ID': ', '.join(d.transaction_ids),
                    'Severity': d.severity,
                    'Amount': ', '.join(str(a) for a in d.amounts),
                    'Explanation': d.explanation
                })
            disc_df = pd.DataFrame(disc_data)
            csv = disc_df.to_csv(index=False)
            st.download_button(
                label="🚨 Discrepancies (CSV)",
                data=csv,
                file_name="reconciliation_discrepancies.csv",
                mime="text/csv"
            )
        else:
            st.info("No discrepancies to download")
    
    with col3:
        # Download raw platform data
        if st.session_state.platform_df is not None:
            csv = st.session_state.platform_df.to_csv(index=False)
            st.download_button(
                label="💳 Platform Data (CSV)",
                data=csv,
                file_name="payment_platform.csv",
                mime="text/csv"
            )
    
    st.divider()
    
    # Summary Report
    st.subheader("Summary Report")
    summary = f"""
    **Reconciliation Summary**
    
    - **Platform Transactions:** {len(st.session_state.platform_df)}
    - **Bank Records:** {len(st.session_state.bank_df)}
    - **Matched:** {len(st.session_state.results_df)}
    - **Discrepancies:** {len(st.session_state.discrepancies)}
    - **Success Rate:** {(len(st.session_state.results_df)/len(st.session_state.platform_df)*100):.1f}%
    
    **Discrepancy Breakdown:**
    """
    
    disc_types = {}
    for disc in st.session_state.discrepancies:
        disc_types[disc.discrepancy_type] = disc_types.get(disc.discrepancy_type, 0) + 1
    
    for disc_type, count in disc_types.items():
        summary += f"\n- {disc_type}: {count}"
    
    st.text(summary)


