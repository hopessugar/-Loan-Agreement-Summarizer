"""Streamlit frontend for loan summarization service."""

import streamlit as st
import requests
import json
import os


# Page configuration
st.set_page_config(
    page_title="Loan Summarizer",
    page_icon="📄",
    layout="wide"
)

# Title and description
st.title("📄 Loan Agreement Summarizer")
st.markdown("""
This application uses AI to analyze loan agreements and extract key financial information.
Simply paste your loan contract text below and get an instant summary with structured data.
""")

# API endpoint configuration - use environment variable or default
DEFAULT_API_URL = os.getenv("BACKEND_URL", "https://loan-summarizer-api.onrender.com")
API_URL = st.text_input(
    "Backend API URL",
    value=DEFAULT_API_URL,
    help="URL of the FastAPI backend (deployed or local)"
)

st.markdown("---")

# Create two columns for input
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Loan Contract Text")
    contract_text = st.text_area(
        "Enter or paste your loan agreement here",
        height=400,
        placeholder="Paste your loan contract text here...",
        label_visibility="collapsed"
    )

with col2:
    st.subheader("Options")
    target_language = st.selectbox(
        "Summary Language",
        options=["English", "Hindi"],
        index=0,
        help="Select the language for the summary"
    )
    
    st.markdown("###")
    submit_button = st.button(
        "🔍 Analyze Contract",
        type="primary",
        use_container_width=True
    )

st.markdown("---")

# Handle submission
if submit_button:
    # Validate input
    if not contract_text or len(contract_text.strip()) == 0:
        st.error("⚠️ Please enter contract text before submitting.")
    else:
        # Show loading spinner
        with st.spinner("🔄 Analyzing contract... This may take a moment."):
            try:
                # Prepare request payload
                payload = {
                    "contract_text": contract_text,
                    "target_language": target_language
                }
                
                # Send POST request to backend
                response = requests.post(
                    f"{API_URL}/summarize",
                    json=payload,
                    timeout=180  # 3 minute timeout for cold start
                )
                
                # Check if request was successful
                if response.status_code == 200:
                    result = response.json()
                    
                    # Display success message
                    st.success("✅ Analysis complete!")
                    
                    # Display results in organized sections
                    st.markdown("## 📊 Extracted Financial Data")
                    
                    structured_data = result.get("structured_data", {})
                    
                    # Create columns for financial data
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        if structured_data.get("loan_amount"):
                            st.metric("💰 Loan Amount", structured_data["loan_amount"])
                        
                        if structured_data.get("interest_rate"):
                            st.metric("📈 Interest Rate", structured_data["interest_rate"])
                        
                        if structured_data.get("repayment_schedule"):
                            st.metric("📅 Repayment Schedule", structured_data["repayment_schedule"])
                    
                    with col_b:
                        if structured_data.get("total_cost_of_credit"):
                            st.metric("💵 Total Cost", structured_data["total_cost_of_credit"])
                        
                        if structured_data.get("late_fees"):
                            st.metric("⚠️ Late Fees", structured_data["late_fees"])
                        
                        if structured_data.get("confidence_score") is not None:
                            st.metric("🎯 Confidence Score", f"{structured_data['confidence_score']}%")
                    
                    # Display default consequences if present
                    if structured_data.get("default_consequences"):
                        st.markdown("### ⚖️ Default Consequences")
                        st.info(structured_data["default_consequences"])
                    
                    # Display summary
                    st.markdown("## 📝 Plain Language Summary")
                    st.markdown(f"**Language:** {result.get('language', 'N/A')}")
                    st.write(result.get("summary", "No summary available"))
                    
                    # Option to download results
                    st.markdown("---")
                    st.download_button(
                        label="📥 Download Results (JSON)",
                        data=json.dumps(result, indent=2),
                        file_name="loan_analysis.json",
                        mime="application/json"
                    )
                    
                else:
                    # Handle HTTP errors
                    error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
                    error_detail = error_data.get('detail', 'Unknown error occurred')
                    
                    st.error(f"❌ Error {response.status_code}: {error_detail}")
                    
                    # Provide helpful guidance based on status code
                    if response.status_code == 401:
                        st.warning("💡 This appears to be an authentication issue. Please check that the GEMINI_API_KEY is set correctly on the backend.")
                    elif response.status_code == 422:
                        st.warning("💡 The input data was invalid. Please check your contract text and try again.")
                    elif response.status_code == 429:
                        st.warning("💡 Rate limit exceeded. Please wait a moment and try again.")
                    elif response.status_code == 503:
                        st.warning("💡 The service is temporarily unavailable. Please try again in a moment.")
                    
            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to the backend API.")
                st.warning(f"💡 Please ensure the backend is running at {API_URL}")
                
            except requests.exceptions.Timeout:
                st.error("❌ Request timed out.")
                st.warning("💡 The analysis is taking longer than expected. Please try again or use a shorter contract.")
                
            except requests.exceptions.RequestException as e:
                st.error(f"❌ Request failed: {str(e)}")
                
            except Exception as e:
                st.error(f"❌ An unexpected error occurred: {str(e)}")
                st.warning("💡 Please try again or contact support if the issue persists.")
