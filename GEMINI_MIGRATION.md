# Migration to Google Gemini API

This document outlines the changes made to migrate from OpenAI to Google Gemini API.

## Changes Made

### 1. Dependencies (`requirements.txt`)
- **Removed**: `openai>=1.57.0`
- **Added**: `google-generativeai>=0.8.0`

### 2. LLM Client (`loan_summarizer/llm/llm_client.py`)
- Completely rewritten to use Google Gemini API
- Uses `google.generativeai` library instead of `openai`
- Configured for JSON output using `response_mime_type="application/json"`
- Error handling updated for Gemini-specific exceptions:
  - `ResourceExhausted` for rate limiting
  - `ServiceUnavailable` for service issues
  - `DeadlineExceeded` for timeouts
  - `PermissionDenied` for authentication errors
  - `InvalidArgument` for invalid requests

### 3. Application Settings (`app.py`)
- **Changed**: `OPENAI_API_KEY` → `GEMINI_API_KEY`
- **Changed**: `openai_model` → `gemini_model`
- **Default model**: `gpt-4-turbo-preview` → `gemini-1.5-flash`
- Updated startup validation messages
- Updated health check endpoint response

### 4. Frontend (`frontend.py`)
- Updated error message to reference `GEMINI_API_KEY` instead of `OPENAI_API_KEY`

### 5. Documentation (`README.md`)
- Updated prerequisites to mention Google Gemini API
- Changed all references from OpenAI to Gemini
- Updated API key setup instructions
- Updated configuration section
- Updated error handling documentation

### 6. New Files
- `.env.example`: Template for environment variables

## Getting Your Gemini API Key

1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key

## Setup Instructions

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your Gemini API key:**
   
   **Windows (PowerShell):**
   ```powershell
   $env:GEMINI_API_KEY="your-api-key-here"
   ```
   
   **Windows (CMD):**
   ```cmd
   set GEMINI_API_KEY=your-api-key-here
   ```
   
   **Linux/Mac:**
   ```bash
   export GEMINI_API_KEY=your-api-key-here
   ```
   
   **Or create a .env file:**
   ```
   GEMINI_API_KEY=your-api-key-here
   ```

3. **Start the backend:**
   ```bash
   uvicorn app:app --reload
   ```

4. **Start the frontend (new terminal):**
   ```bash
   streamlit run frontend.py
   ```

## Model Options

Gemini offers several models:
- `gemini-1.5-flash` (default) - Fast and efficient
- `gemini-1.5-pro` - More capable, slower
- `gemini-1.0-pro` - Previous generation

To change the model, set the `GEMINI_MODEL` environment variable or update the default in `app.py`.

## API Differences

### OpenAI → Gemini
- **JSON Mode**: OpenAI uses `response_format={"type": "json_object"}`, Gemini uses `response_mime_type="application/json"`
- **Async**: OpenAI has native async client, Gemini requires `asyncio.to_thread()`
- **Error Types**: Different exception classes for error handling
- **Pricing**: Gemini is generally more cost-effective

## Testing

The application should work identically to the OpenAI version. Test with the sample contract:

```bash
# The sample contract is in:
loan_summarizer/sample_data/sample_contract.txt
```

## Troubleshooting

### "Authentication failed"
- Check that your `GEMINI_API_KEY` is set correctly
- Verify the API key is valid at https://makersuite.google.com/app/apikey

### "Rate limit exceeded"
- Gemini has generous free tier limits
- Wait a moment and try again
- Consider upgrading your API plan if needed

### "Service unavailable"
- Gemini API may be temporarily down
- Check status at https://status.cloud.google.com/

## Benefits of Gemini

1. **Cost**: Generally more affordable than OpenAI
2. **Free Tier**: Generous free tier for testing
3. **Performance**: Fast response times with gemini-1.5-flash
4. **Multimodal**: Supports images, video, audio (not used in this app yet)
5. **Long Context**: Supports very long context windows

## Future Enhancements

Potential improvements using Gemini's capabilities:
- Add support for analyzing scanned loan documents (images)
- Use longer context for very large contracts
- Implement caching for repeated analyses
- Add support for more languages (Gemini supports 100+ languages)
