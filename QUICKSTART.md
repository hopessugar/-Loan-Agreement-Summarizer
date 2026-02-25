# Quick Start Guide

## Get Your Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

## Setup (Windows)

1. **Set your API key** (PowerShell):
```powershell
$env:GEMINI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
GEMINI_API_KEY=your-api-key-here
```

2. **Start the backend**:
```powershell
uvicorn app:app --reload
```

3. **Start the frontend** (new terminal):
```powershell
streamlit run frontend.py
```

4. **Open your browser** to http://localhost:8501

## Test with Sample Contract

1. Open `loan_summarizer/sample_data/sample_contract.txt`
2. Copy the entire content
3. Paste it into the Streamlit text area
4. Select language (English or Hindi)
5. Click "Analyze Contract"
6. View the results!

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

## Troubleshooting

**"Gemini API key not found"**
- Make sure you set the `GEMINI_API_KEY` environment variable
- Or create a `.env` file with your key

**"Could not connect to backend"**
- Make sure the backend is running on port 8000
- Check the backend terminal for errors

**"Rate limit exceeded"**
- Wait a moment and try again
- Gemini has free tier rate limits

## What Gets Extracted

The system extracts:
- 💰 Loan Amount
- 📈 Interest Rate  
- 📅 Repayment Schedule
- 💵 Total Cost of Credit
- ⚠️ Late Fees
- ⚖️ Default Consequences
- 📝 Plain Language Summary
- 🎯 Confidence Score

Enjoy! 🎉
