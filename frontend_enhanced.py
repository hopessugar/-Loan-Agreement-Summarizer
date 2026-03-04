"""Enhanced Streamlit frontend for loan summarization service with all features."""

import streamlit as st
import requests
import json
import os


# Page configuration
st.set_page_config(
    page_title="Loan Agreement Analyzer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint configuration
DEFAULT_API_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
API_URL = st.sidebar.text_input(
    "Backend API URL",
    value=DEFAULT_API_URL,
    help="URL of the FastAPI backend"
)

# Title and description
st.title("📄 Loan Agreement Intelligence Tool")
st.markdown("""
Comprehensive AI-powered analysis of loan agreements. Extract financial data, detect hidden costs, 
simplify clauses, generate payment timelines, and identify contradictions.
""")

st.markdown("---")

# Sidebar for contract input
with st.sidebar:
    st.header("📝 Contract Input")
    
    # Option to load sample contract
    if st.button("📋 Load Sample Contract"):
        try:
            with open("loan_summarizer/sample_data/sample_contract.txt", "r") as f:
                st.session_state.contract_text = f.read()
                st.success("Sample contract loaded!")
        except:
            st.error("Sample contract not found")
    
    contract_text = st.text_area(
        "Paste your loan agreement here",
        height=300,
        placeholder="Paste your loan contract text here...",
        key="contract_input",
        value=st.session_state.get("contract_text", "")
    )
    
    st.markdown("---")
    
    # Analysis options
    st.header("⚙️ Analysis Options")
    
    target_language = st.selectbox(
        "Summary Language",
        options=["English", "Hindi"],
        index=0
    )
    
    reading_level = st.selectbox(
        "Simplification Level",
        options=["loan_officer", "borrower", "low_literacy"],
        index=1,
        format_func=lambda x: {
            "loan_officer": "Loan Officer (Professional)",
            "borrower": "Borrower (Standard)",
            "low_literacy": "Low Literacy (Simple)"
        }[x]
    )
    
    st.markdown("---")
    
    analyze_button = st.button(
        "🔍 Analyze Contract",
        type="primary",
        use_container_width=True
    )

# Main content area with tabs
if contract_text and len(contract_text.strip()) > 0:
    if analyze_button:
        with st.spinner("🔄 Analyzing contract... This may take a moment."):
            # Store results in session state
            st.session_state.analysis_complete = False
            st.session_state.errors = []
            
            # Call all API endpoints
            try:
                # 1. Basic Summarization
                with st.spinner("Extracting structured data..."):
                    summary_response = requests.post(
                        f"{API_URL}/summarize",
                        json={
                            "contract_text": contract_text,
                            "target_language": target_language
                        },
                        timeout=120
                    )
                    if summary_response.status_code == 200:
                        st.session_state.summary_data = summary_response.json()
                    else:
                        st.session_state.errors.append(f"Summarization: {summary_response.json().get('detail', 'Unknown error')}")
                
                # 2. Cost Analysis
                with st.spinner("Analyzing hidden costs..."):
                    costs_response = requests.post(
                        f"{API_URL}/analyze/costs",
                        json={"contract_text": contract_text},
                        timeout=60
                    )
                    if costs_response.status_code == 200:
                        st.session_state.costs_data = costs_response.json()
                    else:
                        st.session_state.errors.append(f"Cost Analysis: {costs_response.json().get('detail', 'Unknown error')}")
                
                # 3. Timeline
                with st.spinner("Generating payment timeline..."):
                    timeline_response = requests.post(
                        f"{API_URL}/analyze/timeline",
                        json={"contract_text": contract_text},
                        timeout=60
                    )
                    if timeline_response.status_code == 200:
                        st.session_state.timeline_data = timeline_response.json()
                    else:
                        st.session_state.errors.append(f"Timeline: {timeline_response.json().get('detail', 'Unknown error')}")
                
                # 4. Contradictions
                with st.spinner("Detecting contradictions..."):
                    contradictions_response = requests.post(
                        f"{API_URL}/detect/contradictions",
                        json={"contract_text": contract_text},
                        timeout=60
                    )
                    if contradictions_response.status_code == 200:
                        st.session_state.contradictions_data = contradictions_response.json()
                    else:
                        st.session_state.errors.append(f"Contradictions: {contradictions_response.json().get('detail', 'Unknown error')}")
                
                st.session_state.analysis_complete = True
                st.session_state.reading_level = reading_level
                
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to the backend API.")
                st.warning(f"💡 Please ensure the backend is running at {API_URL}")
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out.")
                st.warning("💡 The analysis is taking longer than expected. Please try again.")
            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {str(e)}")

# Display results if analysis is complete
if st.session_state.get("analysis_complete", False):
    
    # Show any errors
    if st.session_state.get("errors"):
        with st.expander("⚠️ Some analyses failed", expanded=False):
            for error in st.session_state.errors:
                st.warning(error)
    
    # Create tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Summary",
        "💰 Hidden Costs",
        "📝 Simplify Clauses",
        "📅 Payment Timeline",
        "⚠️ Contradictions"
    ])
    
    # Tab 1: Summary
    with tab1:
        if "summary_data" in st.session_state:
            st.header("📊 Loan Summary")
            
            data = st.session_state.summary_data
            structured = data.get("structured_data", {})
            
            # Display metrics in columns
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if structured.get("loan_amount"):
                    st.metric("💰 Loan Amount", structured["loan_amount"])
                if structured.get("interest_rate"):
                    st.metric("📈 Interest Rate", structured["interest_rate"])
            
            with col2:
                if structured.get("repayment_schedule"):
                    st.metric("📅 Repayment Schedule", structured["repayment_schedule"])
                if structured.get("total_cost_of_credit"):
                    st.metric("💵 Total Cost", structured["total_cost_of_credit"])
            
            with col3:
                if structured.get("late_fees"):
                    st.metric("⚠️ Late Fees", structured["late_fees"])
                if structured.get("confidence_score") is not None:
                    st.metric("🎯 Confidence Score", f"{structured['confidence_score']}%")
            
            # Default consequences
            if structured.get("default_consequences"):
                st.markdown("### ⚖️ Default Consequences")
                st.info(structured["default_consequences"])
            
            # Plain language summary
            st.markdown("### 📝 Plain Language Summary")
            st.markdown(f"**Language:** {data.get('language', 'N/A')}")
            st.write(data.get("summary", "No summary available"))
            
            # Download option
            st.markdown("---")
            st.download_button(
                label="📥 Download Results (JSON)",
                data=json.dumps(data, indent=2),
                file_name="loan_analysis.json",
                mime="application/json"
            )
        else:
            st.info("Summary data not available")
    
    # Tab 2: Hidden Costs
    with tab2:
        if "costs_data" in st.session_state:
            st.header("💰 Hidden Cost Analysis")
            
            costs = st.session_state.costs_data
            
            # Summary metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if costs.get("loan_amount"):
                    st.metric("Loan Amount", costs["loan_amount"])
            
            with col2:
                st.metric("Total Fees", costs.get("total_fees", "$0.00"))
            
            with col3:
                st.metric("Total Cost", costs.get("total_cost", "$0.00"))
            
            if costs.get("effective_rate"):
                st.metric("Effective Cost Rate", costs["effective_rate"])
            
            # Fee breakdown
            if costs.get("fees"):
                st.markdown("### 📋 Fee Breakdown")
                
                # Group fees by type
                fees_by_type = {}
                for fee in costs["fees"]:
                    fee_type = fee["type"]
                    if fee_type not in fees_by_type:
                        fees_by_type[fee_type] = []
                    fees_by_type[fee_type].append(fee)
                
                # Display fees by category
                for fee_type, fees in fees_by_type.items():
                    with st.expander(f"{fee_type.replace('_', ' ').title()} ({len(fees)} item(s))", expanded=True):
                        for fee in fees:
                            col_a, col_b = st.columns([3, 1])
                            with col_a:
                                st.write(f"**{fee['description']}**")
                                if fee.get("location"):
                                    st.caption(fee["location"][:100] + "...")
                            with col_b:
                                st.write(f"**{fee['amount']}**")
            else:
                st.info("No additional fees detected")
            
            # Interest amount
            if costs.get("interest_amount"):
                st.markdown("### 📈 Interest Charges")
                st.metric("Total Interest", costs["interest_amount"])
        else:
            st.info("Cost analysis data not available")
    
    # Tab 3: Simplify Clauses
    with tab3:
        st.header("📝 Clause Simplification")
        
        st.markdown("""
        Select any clause from your contract to simplify it to your chosen reading level.
        """)
        
        clause_to_simplify = st.text_area(
            "Enter a clause to simplify",
            height=150,
            placeholder="Paste a legal clause here...",
            help="Copy any clause from your contract that you want to understand better"
        )
        
        if st.button("✨ Simplify This Clause"):
            if clause_to_simplify and len(clause_to_simplify.strip()) > 0:
                with st.spinner("Simplifying clause..."):
                    try:
                        simplify_response = requests.post(
                            f"{API_URL}/simplify/clause",
                            json={
                                "clause_text": clause_to_simplify,
                                "reading_level": st.session_state.get("reading_level", "borrower")
                            },
                            timeout=60
                        )
                        
                        if simplify_response.status_code == 200:
                            result = simplify_response.json()
                            
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("#### Original")
                                st.info(result["original_text"])
                                if result.get("original_score"):
                                    score = result["original_score"]
                                    if score.get("flesch_kincaid_grade"):
                                        st.caption(f"Reading Level: Grade {score['flesch_kincaid_grade']}")
                            
                            with col2:
                                st.markdown("#### Simplified")
                                st.success(result["simplified_text"])
                                if result.get("simplified_score"):
                                    score = result["simplified_score"]
                                    if score.get("flesch_kincaid_grade"):
                                        st.caption(f"Reading Level: Grade {score['flesch_kincaid_grade']}")
                            
                            if result.get("improvement_percentage"):
                                st.metric("Improvement", f"{result['improvement_percentage']}% easier to read")
                        else:
                            st.error(f"Simplification failed: {simplify_response.json().get('detail', 'Unknown error')}")
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter a clause to simplify")
    
    # Tab 4: Payment Timeline
    with tab4:
        if "timeline_data" in st.session_state:
            st.header("📅 Payment Timeline")
            
            timeline = st.session_state.timeline_data
            
            # Summary info
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if timeline.get("start_date"):
                    st.metric("Start Date", timeline["start_date"])
            
            with col2:
                if timeline.get("end_date"):
                    st.metric("End Date", timeline["end_date"])
            
            with col3:
                if timeline.get("total_payments"):
                    st.metric("Total Payments", timeline["total_payments"])
            
            if timeline.get("payment_frequency"):
                st.info(f"Payment Frequency: {timeline['payment_frequency'].title()}")
            
            # Timeline events
            if timeline.get("events"):
                st.markdown("### 📋 Payment Schedule")
                
                # Show first 20 events
                events_to_show = timeline["events"][:20]
                
                for event in events_to_show:
                    col_a, col_b, col_c = st.columns([2, 3, 2])
                    
                    with col_a:
                        st.write(f"**{event['date']}**")
                    
                    with col_b:
                        st.write(event['description'])
                    
                    with col_c:
                        if event.get('amount'):
                            st.write(f"**{event['amount']}**")
                
                if len(timeline["events"]) > 20:
                    st.info(f"... and {len(timeline['events']) - 20} more payments")
                
                # Calendar export info
                st.markdown("---")
                st.info("💡 Calendar export (.ics) feature coming soon!")
            else:
                st.warning("No payment events found in the contract")
        else:
            st.info("Timeline data not available")
    
    # Tab 5: Contradictions
    with tab5:
        if "contradictions_data" in st.session_state:
            st.header("⚠️ Contradiction Detection")
            
            report = st.session_state.contradictions_data
            
            if report.get("total_count", 0) == 0:
                st.success("✅ No contradictions detected!")
                st.info("The contract appears to be internally consistent.")
            else:
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total", report.get("total_count", 0))
                
                with col2:
                    st.metric("🔴 High", report.get("high_severity_count", 0))
                
                with col3:
                    st.metric("🟡 Medium", report.get("medium_severity_count", 0))
                
                with col4:
                    st.metric("🟢 Low", report.get("low_severity_count", 0))
                
                # List contradictions
                st.markdown("### 📋 Detected Contradictions")
                
                for i, contradiction in enumerate(report.get("contradictions", []), 1):
                    severity_color = {
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢"
                    }.get(contradiction["severity"], "⚪")
                    
                    with st.expander(
                        f"{severity_color} {i}. {contradiction['type'].replace('_', ' ').title()} - {contradiction['severity'].upper()}",
                        expanded=True
                    ):
                        st.write(f"**Description:** {contradiction['description']}")
                        st.write(f"**Conflicting Values:** {', '.join(contradiction['values'])}")
                        st.write(f"**Found in:** {', '.join(contradiction['locations'])}")
        else:
            st.info("Contradiction detection data not available")

else:
    # Show instructions when no contract is entered
    st.info("👈 Please paste a loan contract in the sidebar and click 'Analyze Contract' to begin.")
    
    st.markdown("""
    ### Features:
    
    - **📊 Summary**: Extract structured financial data and generate plain language summaries
    - **💰 Hidden Costs**: Detect and classify all fees, calculate total cost
    - **📝 Simplify Clauses**: Convert legal language to simple, understandable text
    - **📅 Payment Timeline**: Visualize payment schedule and obligations
    - **⚠️ Contradictions**: Identify inconsistencies in the contract
    
    ### How to Use:
    
    1. Paste your loan agreement in the sidebar
    2. Choose your preferred language and reading level
    3. Click "Analyze Contract"
    4. Explore the results in different tabs
    """)
