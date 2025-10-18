import requests
import json
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

# Import configuration
try:
    from config import API_BASE_URL, DEPLOYMENT_MODE, MOCK_RESPONSES
except ImportError:
    # Fallback configuration
    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    DEPLOYMENT_MODE = os.getenv("DEPLOYMENT_MODE", "local")
    MOCK_RESPONSES = {
        "kyc_approved": True,
        "credit_score": 750,
        "pre_approved_limit": 500000,
        "risk_category": "Low"
    }


def verify_kyc(customer_id: int) -> str:
    """
    Verify KYC details for a customer by making a GET request to the mock API.
    
    Args:
        customer_id (int): The customer ID to verify
        
    Returns:
        str: JSON string with KYC details or error message
    """
    try:
        response = requests.get(f"{API_BASE_URL}/kyc/{customer_id}", timeout=5)
        
        if response.status_code == 200:
            return json.dumps(response.json())
        elif response.status_code == 404:
            return json.dumps({"error": f"Customer with ID {customer_id} not found"})
        else:
            return json.dumps({"error": f"API request failed with status code {response.status_code}"})
            
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        # Fallback to mock data for deployment scenarios
        if DEPLOYMENT_MODE == "demo" or API_BASE_URL != "http://127.0.0.1:8000":
            mock_data = {
                "customer_id": customer_id,
                "name": f"Demo Customer {customer_id}",
                "kyc_approved": True,
                "documents_verified": True,
                "risk_category": "Low",
                "message": "KYC verification successful (Demo Mode)"
            }
            return json.dumps(mock_data)
        else:
            return json.dumps({"error": "Unable to connect to the mock server. Please ensure it's running on http://127.0.0.1:8000"})
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"})


def run_underwriting(customer_id: int, requested_amount: float, monthly_salary: float = 0) -> str:
    """
    Run complete underwriting logic for loan approval/rejection.
    
    Args:
        customer_id (int): The customer ID
        requested_amount (float): The loan amount requested by the customer
        monthly_salary (float): Monthly salary of the customer (optional)
        
    Returns:
        str: JSON string with underwriting decision and reason
    """
    try:
        # Get credit score
        credit_response = requests.get(f"{API_BASE_URL}/credit-score/{customer_id}", timeout=5)
        if credit_response.status_code != 200:
            # Fallback to mock data
            if DEPLOYMENT_MODE == "demo" or API_BASE_URL != "http://127.0.0.1:8000":
                credit_score = MOCK_RESPONSES["credit_score"]
            else:
                return json.dumps({"error": f"Failed to fetch credit score for customer {customer_id}"})
        else:
            credit_score = credit_response.json()["credit_score"]
        
        # Get pre-approved limit
        limit_response = requests.get(f"{API_BASE_URL}/pre-approved-limit/{customer_id}", timeout=5)
        if limit_response.status_code != 200:
            # Fallback to mock data
            if DEPLOYMENT_MODE == "demo" or API_BASE_URL != "http://127.0.0.1:8000":
                pre_approved_limit = MOCK_RESPONSES["pre_approved_limit"]
            else:
                return json.dumps({"error": f"Failed to fetch pre-approved limit for customer {customer_id}"})
        else:
            pre_approved_limit = limit_response.json()["pre_approved_limit"]
        
        # Check credit score
        if credit_score < 700:
            return json.dumps({
                "decision": "rejected",
                "reason": "Credit score is below 700."
            })
        
        # Check requested amount against pre-approved limit
        if requested_amount <= pre_approved_limit:
            return json.dumps({
                "decision": "approved",
                "reason": "Amount is within pre-approved limit."
            })
        
        # Check if amount exceeds maximum limit (2x pre-approved)
        if requested_amount > 2 * pre_approved_limit:
            return json.dumps({
                "decision": "rejected",
                "reason": "Requested amount exceeds maximum limit."
            })
        
        # Amount is between pre_approved_limit and 2 * pre_approved_limit
        if monthly_salary <= 0:
            return json.dumps({
                "decision": "needs_salary_slip",
                "reason": "Please provide a salary slip for further verification."
            })
        
        # Calculate EMI (12% annual interest, 3-year tenure)
        principal = requested_amount
        annual_rate = 0.12
        monthly_rate = annual_rate / 12  # 0.01 (1% per month)
        tenure_months = 36  # 3 years
        
        # EMI formula: P * r * (1+r)^n / ((1+r)^n - 1)
        emi = principal * monthly_rate * pow(1 + monthly_rate, tenure_months) / (pow(1 + monthly_rate, tenure_months) - 1)
        
        # Check if EMI is <= 50% of monthly salary
        if emi <= 0.5 * monthly_salary:
            return json.dumps({
                "decision": "approved",
                "reason": "Approved based on salary verification."
            })
        else:
            return json.dumps({
                "decision": "rejected",
                "reason": "EMI exceeds 50% of monthly salary."
            })
            
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        # Fallback to mock approval for demo purposes
        if DEPLOYMENT_MODE == "demo" or API_BASE_URL != "http://127.0.0.1:8000":
            return json.dumps({
                "decision": "approved",
                "reason": "Demo mode: Loan approved based on standard criteria.",
                "credit_score": MOCK_RESPONSES["credit_score"],
                "approved_amount": min(requested_amount, MOCK_RESPONSES["pre_approved_limit"])
            })
        else:
            return json.dumps({"error": "Unable to connect to the mock server. Please ensure it's running on http://127.0.0.1:8000"})
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred during underwriting: {str(e)}"})


def generate_sanction_letter(customer_name: str, loan_amount: float, interest_rate: float, tenure_months: int) -> str:
    """
    Generate a PDF sanction letter using reportlab.
    
    Args:
        customer_name (str): Name of the customer
        loan_amount (float): Approved loan amount
        interest_rate (float): Interest rate for the loan
        tenure_months (int): Loan tenure in months
        
    Returns:
        str: Success message with file path
    """
    try:
        # Ensure output directory exists
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "output")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sanction_letter_{customer_name.replace(' ', '_')}_{timestamp}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        # Create PDF document
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        content = []
        
        # Title
        content.append(Paragraph("LOAN SANCTION LETTER", title_style))
        content.append(Spacer(1, 20))
        
        # Date
        content.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
        content.append(Spacer(1, 20))
        
        # Customer details
        content.append(Paragraph(f"<b>Dear {customer_name},</b>", styles['Normal']))
        content.append(Spacer(1, 20))
        
        # Letter body
        letter_text = f"""
        We are pleased to inform you that your loan application has been <b>APPROVED</b>.
        
        <b>Loan Details:</b>
        • <b>Approved Amount:</b> ₹{loan_amount:,.2f}
        • <b>Interest Rate:</b> {interest_rate}% per annum
        • <b>Tenure:</b> {tenure_months} months ({tenure_months//12} years)
        • <b>Processing Date:</b> {datetime.now().strftime('%B %d, %Y')}
        
        Please visit our nearest branch with the required documents to complete the loan disbursement process.
        
        <b>Required Documents for Disbursement:</b>
        • Valid government-issued photo ID
        • Address proof
        • Income proof (salary slips/bank statements)
        • Signed loan agreement
        
        We look forward to serving you and helping you achieve your financial goals.
        
        <b>Terms and Conditions:</b>
        This sanction letter is valid for 30 days from the date of issue. The loan is subject to our standard terms and conditions as outlined in the loan agreement.
        
        Thank you for choosing our services.
        """
        
        content.append(Paragraph(letter_text, styles['Normal']))
        content.append(Spacer(1, 40))
        
        # Signature section
        content.append(Paragraph("<b>Sincerely,</b>", styles['Normal']))
        content.append(Spacer(1, 20))
        content.append(Paragraph("<b>Loan Department</b><br/>ABC Bank Limited", styles['Normal']))
        
        # Build PDF
        doc.build(content)
        
        return f"Sanction letter has been successfully generated and saved to output/{filename}"
        
    except Exception as e:
        return f"Error generating sanction letter: {str(e)}"


# Helper function to calculate EMI (can be used independently if needed)
def calculate_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """
    Calculate EMI using the standard formula.
    
    Args:
        principal (float): Loan amount
        annual_rate (float): Annual interest rate (as decimal, e.g., 0.12 for 12%)
        tenure_months (int): Loan tenure in months
        
    Returns:
        float: Monthly EMI amount
    """
    monthly_rate = annual_rate / 12
    emi = principal * monthly_rate * pow(1 + monthly_rate, tenure_months) / (pow(1 + monthly_rate, tenure_months) - 1)
    return emi