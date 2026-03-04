# Loan Agreement Intelligence Tool - Quick Start Guide

## 🚀 Getting Started

### Option 1: Use Deployed Version (Recommended)

The application is already deployed and ready to use!

**Frontend**: Deploy `frontend_enhanced.py` to Streamlit Cloud
**Backend**: https://loan-summarizer-api.onrender.com

### Option 2: Run Locally

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set environment variable
export HUGGINGFACE_API_KEY=your_huggingface_api_key_here

# 3. Start backend (Terminal 1)
python -m uvicorn app:app --reload

# 4. Start enhanced frontend (Terminal 2)
streamlit run frontend_enhanced.py
```

## 📱 Using the Application

### Step 1: Load a Contract
- Click "📋 Load Sample Contract" in the sidebar, OR
- Paste your own loan agreement text

### Step 2: Configure Options
- **Summary Language**: Choose English or Hindi
- **Simplification Level**: 
  - Loan Officer (Professional)
  - Borrower (Standard) 
  - Low Literacy (Simple)

### Step 3: Analyze
- Click "🔍 Analyze Contract"
- Wait 30-60 seconds for first analysis (cold start)
- Subsequent analyses are much faster!

### Step 4: Explore Results
Navigate through 5 tabs:

1. **📊 Summary** - Structured financial data
2. **💰 Hidden Costs** - Fee breakdown and analysis
3. **📝 Simplify Clauses** - Interactive clause simplification
4. **📅 Payment Timeline** - Payment schedule
5. **⚠️ Contradictions** - Inconsistency detection

## 🎯 Features

### 1. Hidden Cost Revealer
- Detects ALL monetary values in contract
- Classifies fees by type (processing, insurance, etc.)
- Calculates total cost and effective rate

### 2. Clause Simplifier
- 3 reading levels for different audiences
- LLM-powered simplification
- Shows readability improvement metrics

### 3. Readability Metrics
- Flesch-Kincaid Grade Level
- Multiple readability scores
- Reading level interpretation

### 4. Payment Timeline
- Extracts payment schedule
- Visualizes obligations
- Calendar export support

### 5. Contradiction Detector
- Finds conflicting values
- Severity classification
- Detailed reports

## ⚡ Performance Tips

### First Request (Cold Start)
- Takes 30-60 seconds
- Backend needs to wake up
- Be patient!

### Subsequent Requests
- Much faster (5-10 seconds)
- Backend stays warm
- Smooth experience

## 🔧 Troubleshooting

### "Cannot connect to backend"
- Backend may be starting up (wait 30 seconds)
- Check backend URL is correct
- Try refreshing the page

### "Request timed out"
- Normal on first request
- Try again - should work second time
- Backend is warming up

### "Analysis failed"
- Check contract text is valid
- Try with sample contract first
- Check backend logs for errors

## 📊 API Endpoints

All endpoints available at: https://loan-summarizer-api.onrender.com

- `GET /` - API information
- `GET /health` - Health check
- `GET /docs` - Interactive documentation
- `POST /summarize` - Basic summarization
- `POST /analyze/costs` - Hidden cost analysis
- `POST /simplify/clause` - Clause simplification
- `POST /analyze/timeline` - Timeline generation
- `POST /detect/contradictions` - Contradiction detection

## 💡 Tips for Best Results

1. **Use well-formatted contracts** - Clear structure works best
2. **Check confidence scores** - Low scores may indicate issues
3. **Verify extracted data** - Always double-check critical values
4. **Try different reading levels** - Find what works for your audience
5. **Download results** - Save JSON for your records

## 🆘 Need Help?

- **API Documentation**: https://loan-summarizer-api.onrender.com/docs
- **GitHub Repository**: https://github.com/hopessugar/-Loan-Agreement-Summarizer
- **Sample Contracts**: Available in `loan_summarizer/sample_data/`

## 🎉 You're Ready!

Start analyzing loan contracts now with the most comprehensive AI-powered tool available!

---

**Version**: 0.2.0  
**Last Updated**: 2024  
**Powered by**: Hugging Face LLM (meta-llama/Llama-3.2-3B-Instruct)
