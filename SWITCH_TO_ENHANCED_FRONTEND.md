# 🔄 Switch to Enhanced Frontend

## Current Issue

You're seeing only the basic summary because you're running `frontend.py` (the simple version).

To see ALL 5 features with tabs, you need to run `frontend_enhanced.py`.

## Quick Fix

### Option 1: Use the Batch File (Easiest)

1. **Stop the current frontend** (Ctrl+C in the terminal)
2. **Double-click**: `run_enhanced_frontend.bat`
3. **Wait** for browser to open
4. **Enjoy** all 5 features!

### Option 2: Manual Command

1. **Stop the current frontend** (Ctrl+C in the terminal)
2. **Run this command**:
   ```bash
   streamlit run frontend_enhanced.py
   ```
3. **Open browser** to http://localhost:8501

## What You'll See

### Enhanced Frontend (frontend_enhanced.py) - 5 TABS:

1. **📊 Summary** - What you're seeing now
2. **💰 Hidden Costs** - Fee breakdown and analysis
3. **📝 Simplify Clauses** - Interactive clause simplification
4. **📅 Payment Timeline** - Payment schedule visualization
5. **⚠️ Contradictions** - Inconsistency detection

### Simple Frontend (frontend.py) - 1 PAGE:

- Only basic summary (what you're currently seeing)

## Step-by-Step Instructions

### Windows:

1. Open Command Prompt or PowerShell
2. Navigate to your project folder:
   ```bash
   cd path\to\loan-agreement-summarizer
   ```
3. Stop any running Streamlit (Ctrl+C)
4. Run enhanced frontend:
   ```bash
   streamlit run frontend_enhanced.py
   ```

### Alternative - Use the Batch File:

1. Find `run_enhanced_frontend.bat` in your project folder
2. Double-click it
3. Browser will open automatically

## Verify You're Running the Right Frontend

### Enhanced Frontend Shows:
- ✅ 5 tabs at the top
- ✅ Backend connection status (expandable)
- ✅ Quick tips in sidebar
- ✅ Multiple features

### Simple Frontend Shows:
- ❌ Only one page
- ❌ No tabs
- ❌ Just basic summary

## Still Not Working?

### Check 1: Which file is running?
Look at the terminal - it should say:
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

And the command should be:
```bash
streamlit run frontend_enhanced.py
```

### Check 2: Clear browser cache
1. Press Ctrl+Shift+R to hard refresh
2. Or clear browser cache
3. Reload the page

### Check 3: Stop all Streamlit processes
```bash
# Windows
taskkill /F /IM streamlit.exe

# Then restart
streamlit run frontend_enhanced.py
```

## Quick Comparison

| Feature | frontend.py | frontend_enhanced.py |
|---------|-------------|---------------------|
| Summary | ✅ | ✅ |
| Hidden Costs | ❌ | ✅ |
| Simplify Clauses | ❌ | ✅ |
| Payment Timeline | ❌ | ✅ |
| Contradictions | ❌ | ✅ |
| Tabs | ❌ | ✅ |
| Backend Status | ❌ | ✅ |
| Quick Tips | ❌ | ✅ |

## Need Help?

If you're still seeing only the summary page:

1. **Check the terminal** - what command did you run?
2. **Check the browser URL** - should be localhost:8501
3. **Try the batch file** - `run_enhanced_frontend.bat`
4. **Restart everything** - stop all, then run enhanced version

---

**Remember**: You want `frontend_enhanced.py` for all features! 🚀
