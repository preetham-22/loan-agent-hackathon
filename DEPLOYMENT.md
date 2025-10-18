# Streamlit Cloud Deployment Guide

## 🚀 Quick Deployment Steps

### 1. Repository Setup (✅ Already Done)
- Your GitHub repository is ready at: https://github.com/preetham-22/loan-agent-hackathon

### 2. Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**: Visit [share.streamlit.io](https://share.streamlit.io)

2. **Sign in with GitHub**: Use your GitHub account

3. **Create New App**:
   - Repository: `preetham-22/loan-agent-hackathon`
   - Branch: `main`
   - Main file path: `app/main.py`

4. **Add Secrets** (Required):
   - Click "Advanced settings" before deploying
   - Add to secrets.toml:
   ```toml
   OPENAI_API_KEY = "your_openai_api_key_here"
   DEPLOYMENT_MODE = "demo"
   API_BASE_URL = "demo"
   ```

5. **Deploy**: Click "Deploy!" and wait for deployment

### 3. Demo Mode Features

When deployed to Streamlit Cloud (without the FastAPI backend), the app automatically:
- ✅ Uses mock customer data for demonstration
- ✅ Simulates KYC verification with realistic responses
- ✅ Performs loan underwriting with standard business logic
- ✅ Generates professional PDF sanction letters
- ✅ Maintains full chat interface functionality

### 4. Expected Behavior

**Demo Mode Responses**:
- Credit Score: 750 (Good)
- Pre-approved Limit: ₹5,00,000
- KYC Status: Approved
- Risk Category: Low

**Test Customer IDs**: CUST001 to CUST010 (all work in demo mode)

### 5. Local Development vs Cloud Deployment

| Feature | Local (with FastAPI) | Cloud (Demo Mode) |
|---------|---------------------|------------------|
| KYC Verification | Real API calls | Mock responses |
| Credit Scoring | Dynamic data | Standard values |
| Underwriting | Full logic | Simplified logic |
| PDF Generation | ✅ Full | ✅ Full |
| Chat Interface | ✅ Full | ✅ Full |

### 6. Production Considerations

For a production deployment:
1. Deploy FastAPI backend to a cloud service (Railway, Render, etc.)
2. Update `API_BASE_URL` in secrets to point to your deployed API
3. Set `DEPLOYMENT_MODE` to "production"
4. Integrate with real banking APIs
5. Add proper authentication and security measures

---

**Note**: The current setup is optimized for demonstration and hackathon purposes. The demo mode ensures your Streamlit app works perfectly even without the backend services running.