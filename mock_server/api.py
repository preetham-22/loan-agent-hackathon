from fastapi import FastAPI, HTTPException, File, UploadFile
from typing import Optional
import json
import os

app = FastAPI(title="Loan Agent Mock Server", version="1.0.0")

# Load dummy data at startup
customers_data = []

@app.on_event("startup")
async def load_data():
    global customers_data
    try:
        # Get the directory of this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_file_path = os.path.join(current_dir, "dummy_data.json")
        
        with open(json_file_path, 'r') as file:
            customers_data = json.load(file)
        print(f"Loaded {len(customers_data)} customers from dummy_data.json")
    except Exception as e:
        print(f"Error loading dummy data: {e}")
        customers_data = []

def find_customer(customer_id: int):
    """Helper function to find a customer by ID"""
    for customer in customers_data:
        if customer["id"] == customer_id:
            return customer
    return None

@app.get("/")
async def root():
    return {"message": "Loan Agent Mock Server is running", "total_customers": len(customers_data)}

@app.get("/kyc/{customer_id}")
async def get_kyc_info(customer_id: int):
    """Get KYC information (name, phone, address) for a customer"""
    customer = find_customer(customer_id)
    
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")
    
    return {
        "name": customer["name"],
        "phone": customer["phone"],
        "address": customer["address"]
    }

@app.get("/credit-score/{customer_id}")
async def get_credit_score(customer_id: int):
    """Get credit score for a customer"""
    customer = find_customer(customer_id)
    
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")
    
    return {
        "credit_score": customer["credit_score"]
    }

@app.get("/pre-approved-limit/{customer_id}")
async def get_pre_approved_limit(customer_id: int):
    """Get pre-approved limit for a customer"""
    customer = find_customer(customer_id)
    
    if not customer:
        raise HTTPException(status_code=404, detail=f"Customer with ID {customer_id} not found")
    
    return {
        "pre_approved_limit": customer["pre_approved_limit"]
    }

@app.post("/upload-salary-slip")
async def upload_salary_slip(file: UploadFile = File(...)):
    """Simulate salary slip upload for validation"""
    # For this PoC, we just simulate the file upload
    # In a real application, you would process the file here
    
    return {
        "status": "success",
        "message": "Salary slip received for validation.",
        "filename": file.filename,
        "content_type": file.content_type
    }

# Additional endpoint to get all customers (useful for debugging)
@app.get("/customers")
async def get_all_customers():
    """Get all customers (for debugging purposes)"""
    return customers_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)