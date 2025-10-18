"""
Configuration settings for the loan agent application
"""
import os

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# For Streamlit Cloud deployment, you can set this to a deployed FastAPI URL
# or use a mock mode
DEPLOYMENT_MODE = os.getenv("DEPLOYMENT_MODE", "local")

# Mock data for when API is not available
MOCK_RESPONSES = {
    "kyc_approved": True,
    "credit_score": 750,
    "pre_approved_limit": 500000,
    "risk_category": "Low"
}