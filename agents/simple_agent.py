"""
Lightweight agent implementation for Streamlit Cloud deployment
"""
import json
import os
from typing import Dict, Any

def simple_loan_processing(user_input: str) -> Dict[str, Any]:
    """
    Simple loan processing logic for deployment scenarios
    """
    # Extract loan amount from user input using simple string parsing
    words = user_input.lower().split()
    loan_amount = 100000  # default
    
    # Try to find numbers in the input
    for word in words:
        try:
            # Remove common currency symbols and commas
            clean_word = word.replace(',', '').replace('₹', '').replace('$', '')
            if clean_word.isdigit() and len(clean_word) >= 4:  # Likely a loan amount
                loan_amount = float(clean_word)
                break
        except:
            continue
    
    # Determine loan purpose
    purpose = "personal"
    if any(word in user_input.lower() for word in ["home", "house", "property"]):
        purpose = "home"
    elif any(word in user_input.lower() for word in ["business", "commercial"]):
        purpose = "business"
    elif any(word in user_input.lower() for word in ["car", "auto", "vehicle"]):
        purpose = "auto"
    
    # Simple approval logic
    if loan_amount <= 500000:
        decision = "approved"
        reason = f"Loan approved for ₹{loan_amount:,.0f} for {purpose} purpose."
    else:
        decision = "needs_review"
        reason = f"Loan amount ₹{loan_amount:,.0f} requires additional review."
    
    return {
        "loan_amount": loan_amount,
        "purpose": purpose,
        "decision": decision,
        "reason": reason,
        "customer_id": "DEMO001",
        "credit_score": 750,
        "messages": [
            {"role": "assistant", "content": f"I've processed your loan application for ₹{loan_amount:,.0f}. {reason}"}
        ]
    }

def process_loan_application(user_message: str) -> str:
    """
    Main processing function that mimics the LangGraph workflow
    """
    try:
        # Import the full workflow if available
        from agents.graph import app
        result = app.invoke({"messages": [{"role": "user", "content": user_message}]})
        return result["messages"][-1]["content"]
    except (ImportError, Exception) as e:
        # Fallback to simple processing
        print(f"Using fallback processing: {e}")
        result = simple_loan_processing(user_message)
        return result["messages"][0]["content"]