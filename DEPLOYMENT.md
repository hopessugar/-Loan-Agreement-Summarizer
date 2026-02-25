# Deployment Guide

This guide covers deploying the Loan Agreement Summarizer to free hosting platforms.

## Architecture

- **Backend (FastAPI)**: Deployed on Render.com
- **Frontend (Streamlit)**: Deployed on Streamlit Community Cloud

## Backend Deployment (Render.com)

### Prerequisites
- GitHub account with your repository
- Render.com account (free): https://render.com

### Steps

1. **Sign up/Login to Render.com**
   - Go to https://render.com
   - Sign up with your GitHub account

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `hopessugar/-Loan-Agreement-Summarizer`
   - Click "Connect"

3. **Configure Service**
   - **Name**: `loan-summarizer-api` (or your choice)
   - **Region**: Oregon (Free)
   - **Branch**: `main`
   - **Root Directory**: Leave empty
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free

4. **Add Environment Variables**
   - Click "Advanced" → "Add Environment Variable"
   - Add:
     - **Key**: `HUGGINGFACE_API_KEY`
     - **Value**: Your Hugging Face API token (get from https://huggingface.co/settings/tokens)
   - Add:
     - **Key**: `PYTHON_VERSION`
     - **Value**: `3.11.0`

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (5-10 minutes)
   - Copy your backend URL (e.g., `https://loan-summarizer-api.onrender.com`)

### Important Notes
- Free tier sleeps after 15 minutes of inactivity
- First request after sleep takes ~30 seconds to wake up
- 750 hours/month free (enough for personal projects)

## Frontend Deployment (Streamlit Community Cloud)

### Prerequisites
- GitHub account with your repository
- Streamlit Community Cloud account (free): https://streamlit.io/cloud

### Steps

1. **Sign up/Login to Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Sign in with GitHub

2. **Deploy New App**
   - Click "New app"
   - Select your repository: `hopessugar/-Loan-Agreement-Summarizer`
   - **Main file path**: `frontend.py`
   - **Branch**: `main`

3. **Configure Environment Variables**
   - Click "Advanced settings"
   - Add environment variable:
     - **Key**: `BACKEND_URL`
     - **Value**: Your Render backend URL (e.g., `https://loan-summarizer-api.onrender.com`)

4. **Deploy**
   - Click "Deploy!"
   - Wait for deployment (2-3 minutes)
   - Your app will be live at: `https://[your-app-name].streamlit.app`

### Important Notes
- Free tier includes unlimited public apps
- Apps sleep after inactivity but wake instantly
- Automatic redeployment on git push

## Alternative: Deploy Both on Render.com

If you prefer to deploy both on Render:

### Backend
Follow the steps above for backend deployment.

### Frontend
1. Create another Web Service on Render
2. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run frontend.py --server.port $PORT --server.address 0.0.0.0`
   - **Environment Variable**: `BACKEND_URL` = your backend URL

## Post-Deployment Testing

1. **Test Backend**
   ```bash
   curl https://your-backend-url.onrender.com/health
   ```
   Should return: `{"status": "healthy", ...}`

2. **Test Frontend**
   - Visit your Streamlit app URL
   - Paste a sample loan contract
   - Click "Analyze Contract"
   - Verify results appear

## Troubleshooting

### Backend Issues

**Problem**: Service won't start
- Check logs in Render dashboard
- Verify `HUGGINGFACE_API_KEY` is set correctly
- Ensure `requirements.txt` has all dependencies

**Problem**: 401 Authentication Error
- Verify your Hugging Face API key is valid
- Get a new token from https://huggingface.co/settings/tokens

**Problem**: 500 Internal Server Error
- Check Render logs for detailed error
- Verify the model name is correct in `app.py`

### Frontend Issues

**Problem**: Can't connect to backend
- Verify `BACKEND_URL` environment variable is set
- Check backend is running (visit `/health` endpoint)
- Ensure backend URL doesn't have trailing slash

**Problem**: CORS errors
- Backend already has CORS enabled for all origins
- If issues persist, check Render logs

### Performance Issues

**Problem**: First request is slow
- This is normal for free tier (cold start)
- Backend wakes from sleep in ~30 seconds
- Subsequent requests are fast

**Problem**: Request timeout
- Increase timeout in `frontend.py` (currently 120s)
- Consider using a smaller model for faster responses

## Monitoring

### Render Dashboard
- View logs: Render Dashboard → Your Service → Logs
- Monitor usage: Dashboard → Your Service → Metrics
- Check health: Visit `https://your-backend-url.onrender.com/health`

### Streamlit Dashboard
- View logs: Streamlit Cloud → Your App → Logs
- Monitor usage: Streamlit Cloud → Your App → Analytics

## Updating Your Deployment

Both platforms auto-deploy on git push:

```bash
git add .
git commit -m "Update application"
git push origin main
```

- Render: Automatically rebuilds and redeploys
- Streamlit: Automatically redeploys

## Cost Optimization

### Free Tier Limits
- **Render**: 750 hours/month, sleeps after 15 min inactivity
- **Streamlit**: Unlimited public apps, instant wake from sleep

### Tips
- Use smaller models for faster/cheaper inference
- Implement caching for repeated requests
- Monitor API usage on Hugging Face dashboard

## Security Best Practices

1. **Never commit API keys**
   - Always use environment variables
   - Keys are in `.gitignore`

2. **Use HTTPS**
   - Both platforms provide free SSL
   - Always use `https://` URLs

3. **Rate Limiting**
   - Consider adding rate limiting to backend
   - Monitor Hugging Face API usage

4. **Input Validation**
   - Backend validates all inputs
   - Frontend provides user-friendly errors

## Support

- **Render**: https://render.com/docs
- **Streamlit**: https://docs.streamlit.io
- **Hugging Face**: https://huggingface.co/docs

## Next Steps

After deployment:
1. Test with various loan contracts
2. Monitor performance and errors
3. Consider upgrading to paid tiers for production use
4. Add analytics and monitoring
5. Implement user authentication if needed
