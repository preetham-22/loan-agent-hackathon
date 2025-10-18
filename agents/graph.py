from typing import TypedDict, List, Dict, Any, Optional
import json
import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

# Import tool functions
try:
    from agents.tools import verify_kyc, run_underwriting, generate_sanction_letter
except ImportError:
    # Fallback for relative imports
    from .tools import verify_kyc, run_underwriting, generate_sanction_letter

# Load environment variables
load_dotenv()

# Initialize LLM
llm = ChatOpenAI(model="gpt-4o")


# Pydantic model for structured extraction
class InitialQuery(BaseModel):
    """Model for extracting customer ID and loan amount from user messages."""
    customer_id: int = Field(description="The unique ID of the customer")
    requested_amount: float = Field(description="The loan amount the customer is requesting")


class AgentState(TypedDict):
    """
    State class for the LangGraph loan agent workflow.
    
    This state tracks the entire loan application process from customer
    identification through underwriting to final sanction letter generation.
    """
    
    # Customer identification
    customer_id: int
    
    # Loan application details
    requested_amount: float
    monthly_salary: float  # Initially 0, updated when salary slip is provided
    
    # Conversation and interaction history
    messages: List[Dict[str, Any]]  # Stores conversation history and agent messages
    
    # Underwriting and decision tracking
    underwriting_result: Dict[str, Any]  # Structured output from underwriting tool
    
    # Document generation
    sanction_letter_path: str  # Path to generated PDF sanction letter
    
    # Optional: Additional tracking fields
    kyc_verified: Optional[bool]  # Track KYC verification status
    current_step: Optional[str]   # Track current workflow step
    error_message: Optional[str]  # Store any error messages
    
    # Optional: Customer details (cached from KYC)
    customer_name: Optional[str]
    customer_phone: Optional[str]
    customer_address: Optional[str]
    
    # Optional: Financial details (cached from APIs)
    credit_score: Optional[int]
    pre_approved_limit: Optional[float]


# Helper function to initialize a new agent state
def create_initial_state(customer_id: int, requested_amount: float) -> AgentState:
    """
    Create an initial state for a new loan application.
    
    Args:
        customer_id (int): The customer's ID
        requested_amount (float): The requested loan amount
        
    Returns:
        AgentState: Initial state with default values
    """
    return AgentState(
        customer_id=customer_id,
        requested_amount=requested_amount,
        monthly_salary=0.0,
        messages=[],
        underwriting_result={},
        sanction_letter_path="",
        kyc_verified=None,
        current_step="initialization",
        error_message=None,
        customer_name=None,
        customer_phone=None,
        customer_address=None,
        credit_score=None,
        pre_approved_limit=None
    )


# State update helper functions for common operations
def add_message(state: AgentState, role: str, content: str) -> AgentState:
    """Add a message to the conversation history."""
    message = {
        "role": role,
        "content": content,
        "timestamp": None  # Can be filled with actual timestamp if needed
    }
    state["messages"].append(message)
    return state


def update_step(state: AgentState, step: str) -> AgentState:
    """Update the current workflow step."""
    state["current_step"] = step
    return state


def set_error(state: AgentState, error: str) -> AgentState:
    """Set an error message in the state."""
    state["error_message"] = error
    return state


# Workflow step constants
class WorkflowSteps:
    """Constants for different workflow steps."""
    INITIALIZATION = "initialization"
    KYC_VERIFICATION = "kyc_verification"
    UNDERWRITING = "underwriting"
    SALARY_VERIFICATION = "salary_verification"
    DECISION_MAKING = "decision_making"
    SANCTION_LETTER = "sanction_letter"
    COMPLETED = "completed"
    ERROR = "error"


# ========================================
# GRAPH NODE FUNCTIONS
# ========================================

def call_initial_user_interaction_node(state: AgentState) -> dict:
    """
    Process the initial user message to extract customer_id and requested_amount.
    
    Args:
        state (AgentState): Current state with user messages
        
    Returns:
        dict: Updated state with extracted values and confirmation message
    """
    try:
        # Get the last user message
        if not state["messages"]:
            raise ValueError("No messages found in state")
        
        last_message = state["messages"][-1]
        user_content = last_message.get("content", "")
        
        # Use Pydantic structured output for reliable extraction
        llm_with_tool = llm.with_structured_output(InitialQuery)
        
        # Create a simple extraction prompt
        extraction_prompt = f"""Extract the customer ID and requested loan amount from the following user message.
Look for patterns like:
- Customer ID/number (may be preceded by #, "customer", "id", etc.)
- Loan amount (may have currency symbols like $ or ₹, and may include commas)

User message: "{user_content}"

Extract the customer ID as an integer and the loan amount as a float (without currency symbols or commas)."""

        try:
            # Invoke LLM with structured output
            extracted_query = llm_with_tool.invoke(extraction_prompt)
            
            # Access the extracted values from the Pydantic object
            customer_id = extracted_query.customer_id
            requested_amount = extracted_query.requested_amount
            
        except Exception as extraction_error:
            # Fallback to regex if structured extraction fails
            import re
            customer_id_match = re.search(r'customer\s*#?(\d+)', user_content, re.IGNORECASE)
            amount_match = re.search(r'[\$₹]?(\d{1,3}(?:,?\d{3})*(?:\.\d{2})?)', user_content)
            
            if customer_id_match and amount_match:
                customer_id = int(customer_id_match.group(1))
                requested_amount = float(amount_match.group(1).replace(',', ''))
            else:
                error_msg = "Please provide both customer ID and loan amount clearly. Format: 'Customer X needs $Y'"
                state["error_message"] = error_msg
                state["messages"].append({
                    "role": "assistant",
                    "content": error_msg
                })
                return {"messages": state["messages"], "error_message": state["error_message"]}
        
        # Add debugging print statements
        print(f"--- 🕵️ Initial Interaction Node ---")
        print(f"Extracted Customer ID: {customer_id}")
        print(f"Extracted Requested Amount: {requested_amount}")
        
        # Verify KYC to get customer name for personalization
        kyc_result = verify_kyc(customer_id)
        kyc_data = json.loads(kyc_result)
        
        if "error" not in kyc_data:
            customer_name = kyc_data.get("name", f"Customer {customer_id}")
            confirmation_message = f"Got it, {customer_name}. Let me start the loan process for ₹{requested_amount:,.2f} for you."
        else:
            confirmation_message = f"Got it. Let me start the loan process for ₹{requested_amount:,.2f} for customer ID {customer_id}."
        
        # Add confirmation message
        state["messages"].append({
            "role": "assistant",
            "content": confirmation_message
        })
        
        # Update state
        return {
            "customer_id": customer_id,
            "requested_amount": requested_amount,
            "messages": state["messages"],
            "current_step": WorkflowSteps.UNDERWRITING
        }
        
    except Exception as e:
        error_msg = f"Error processing your request: {str(e)}. Please provide customer ID and loan amount clearly."
        state["error_message"] = error_msg
        state["messages"].append({
            "role": "assistant", 
            "content": error_msg
        })
        return {"messages": state["messages"], "error_message": state["error_message"]}


def call_underwriting_node(state: AgentState) -> dict:
    """
    Perform underwriting analysis using the underwriting tool.
    
    Args:
        state (AgentState): Current state with customer and loan details
        
    Returns:
        dict: Updated state with underwriting result
    """
    try:
        # Add debugging print statements at the beginning
        print(f"\n--- 💰 Underwriting Node ---")
        print(f"Running underwriting for Customer ID: {state['customer_id']} with Amount: {state['requested_amount']}")
        
        # Call the underwriting tool
        underwriting_response = run_underwriting(
            customer_id=state["customer_id"],
            requested_amount=state["requested_amount"],
            monthly_salary=state["monthly_salary"]
        )
        
        # Parse JSON response
        underwriting_result = json.loads(underwriting_response)
        
        # Add debugging print statement after getting the result
        print(f"Underwriting Result: {underwriting_result}")
        
        # Update state with result
        state["underwriting_result"] = underwriting_result
        state["current_step"] = WorkflowSteps.DECISION_MAKING
        
        return {
            "underwriting_result": underwriting_result,
            "current_step": state["current_step"]
        }
        
    except Exception as e:
        error_msg = f"Error during underwriting: {str(e)}"
        state["error_message"] = error_msg
        return {"error_message": error_msg}


def call_generate_sanction_letter_node(state: AgentState) -> dict:
    """
    Generate sanction letter for approved loans.
    
    Args:
        state (AgentState): Current state with approval decision
        
    Returns:
        dict: Updated state with sanction letter path and success message
    """
    try:
        # Get customer name (try from KYC first, fallback to generic)
        customer_name = state.get("customer_name")
        if not customer_name:
            kyc_result = verify_kyc(state["customer_id"])
            kyc_data = json.loads(kyc_result)
            customer_name = kyc_data.get("name", f"Customer_{state['customer_id']}")
        
        # Generate sanction letter
        letter_response = generate_sanction_letter(
            customer_name=customer_name,
            loan_amount=state["requested_amount"],
            interest_rate=12.0,  # 12% as per underwriting logic
            tenure_months=36     # 3 years as per underwriting logic
        )
        
        # Update state
        state["sanction_letter_path"] = letter_response
        
        # Add success message
        success_message = (
            f"🎉 Congratulations! Your loan application has been approved. "
            f"Your sanction letter has been generated and is ready for download. "
            f"{letter_response}"
        )
        
        state["messages"].append({
            "role": "assistant",
            "content": success_message
        })
        
        state["current_step"] = WorkflowSteps.COMPLETED
        
        return {
            "sanction_letter_path": state["sanction_letter_path"],
            "messages": state["messages"],
            "current_step": state["current_step"]
        }
        
    except Exception as e:
        error_msg = f"Error generating sanction letter: {str(e)}"
        state["error_message"] = error_msg
        state["messages"].append({
            "role": "assistant",
            "content": f"Your loan is approved, but there was an issue generating the sanction letter: {error_msg}"
        })
        return {"error_message": error_msg, "messages": state["messages"]}


def prepare_rejection_node(state: AgentState) -> dict:
    """
    Prepare a polite rejection message based on underwriting result.
    
    Args:
        state (AgentState): Current state with rejection decision
        
    Returns:
        dict: Updated state with rejection message
    """
    try:
        underwriting_result = state.get("underwriting_result", {})
        reason = underwriting_result.get("reason", "Unable to approve the loan application")
        decision = underwriting_result.get("decision", "rejected")
        
        # Create personalized rejection message
        if decision == "rejected":
            if "credit score" in reason.lower():
                rejection_message = (
                    "I'm sorry, but we cannot approve your loan application at this time. "
                    f"The reason: {reason} "
                    "We recommend working on improving your credit score and reapplying in the future. "
                    "Our financial advisors would be happy to help you with credit improvement strategies."
                )
            elif "exceeds maximum limit" in reason.lower():
                rejection_message = (
                    "I'm sorry, but we cannot approve the requested loan amount. "
                    f"The reason: {reason} "
                    "Please consider applying for a lower amount that falls within your pre-approved limit. "
                    "Our team can help you determine an appropriate loan amount based on your profile."
                )
            elif "EMI exceeds" in reason:
                rejection_message = (
                    "I'm sorry, but we cannot approve your loan application. "
                    f"The reason: {reason} "
                    "The monthly EMI would be too high relative to your income. "
                    "Please consider applying for a lower amount or extending the tenure to reduce the EMI."
                )
            else:
                rejection_message = (
                    f"I'm sorry, but we cannot approve your loan application. {reason} "
                    "Please feel free to contact our customer service for more information "
                    "or to discuss alternative options."
                )
        else:
            rejection_message = f"There was an issue with your application: {reason}"
        
        # Add rejection message to conversation
        state["messages"].append({
            "role": "assistant",
            "content": rejection_message
        })
        
        state["current_step"] = WorkflowSteps.COMPLETED
        
        return {
            "messages": state["messages"],
            "current_step": state["current_step"]
        }
        
    except Exception as e:
        error_msg = f"Error preparing rejection message: {str(e)}"
        state["error_message"] = error_msg
        return {"error_message": error_msg}


# ========================================
# LANGGRAPH WORKFLOW CONSTRUCTION
# ========================================

from langgraph.graph import StateGraph, END


def route_after_underwriting(state: AgentState) -> str:
    """
    Router function to determine the next step after underwriting.
    
    Args:
        state (AgentState): Current state with underwriting result
        
    Returns:
        str: Next node name or END
    """
    underwriting_result = state.get("underwriting_result", {})
    decision = underwriting_result.get("decision", "")
    
    if decision == "approved":
        return "generate_sanction_letter"
    elif decision == "rejected":
        return "handle_rejection"
    elif decision == "needs_salary_slip":
        # For now, end the workflow here - front-end will handle salary slip collection
        return "__end__"
    else:
        # Default to rejection handling for unknown decisions
        return "handle_rejection"


# Create the workflow graph
workflow = StateGraph(AgentState)

# Add nodes to the workflow
workflow.add_node("user_interaction", call_initial_user_interaction_node)
workflow.add_node("underwriting", call_underwriting_node)
workflow.add_node("generate_sanction_letter", call_generate_sanction_letter_node)
workflow.add_node("handle_rejection", prepare_rejection_node)

# Set the entry point
workflow.set_entry_point("user_interaction")

# Add edges between nodes
workflow.add_edge("user_interaction", "underwriting")

# Add conditional edge from underwriting based on decision
workflow.add_conditional_edges(
    "underwriting",
    route_after_underwriting,
    {
        "generate_sanction_letter": "generate_sanction_letter",
        "handle_rejection": "handle_rejection",
        "__end__": END
    }
)

# Add edges to END
workflow.add_edge("generate_sanction_letter", END)
workflow.add_edge("handle_rejection", END)

# Compile the workflow
app = workflow.compile()


# ========================================
# WORKFLOW EXECUTION HELPER
# ========================================

def run_loan_application_workflow(user_message: str) -> AgentState:
    """
    Execute the complete loan application workflow.
    
    Args:
        user_message (str): Initial user message with loan request
        
    Returns:
        AgentState: Final state after workflow completion
    """
    # Create initial state with user message
    initial_state = AgentState(
        customer_id=0,  # Will be extracted from user message
        requested_amount=0.0,  # Will be extracted from user message
        monthly_salary=0.0,
        messages=[{"role": "user", "content": user_message}],
        underwriting_result={},
        sanction_letter_path="",
        kyc_verified=None,
        current_step=WorkflowSteps.INITIALIZATION,
        error_message=None,
        customer_name=None,
        customer_phone=None,
        customer_address=None,
        credit_score=None,
        pre_approved_limit=None
    )
    
    # Execute the workflow
    try:
        final_state = app.invoke(initial_state)
        return final_state
    except Exception as e:
        # Handle workflow execution errors
        initial_state["error_message"] = f"Workflow execution error: {str(e)}"
        initial_state["current_step"] = WorkflowSteps.ERROR
        initial_state["messages"].append({
            "role": "assistant",
            "content": f"I'm sorry, there was an error processing your loan application: {str(e)}"
        })
        return initial_state


def run_loan_application_with_salary(customer_id: int, requested_amount: float, monthly_salary: float) -> AgentState:
    """
    Execute loan application workflow with salary information provided upfront.
    
    Args:
        customer_id (int): Customer ID
        requested_amount (float): Requested loan amount
        monthly_salary (float): Monthly salary for EMI calculation
        
    Returns:
        AgentState: Final state after workflow completion
    """
    # Create initial state with all required information
    initial_state = AgentState(
        customer_id=customer_id,
        requested_amount=requested_amount,
        monthly_salary=monthly_salary,
        messages=[{"role": "user", "content": f"Process loan for customer {customer_id}, amount {requested_amount}, salary {monthly_salary}"}],
        underwriting_result={},
        sanction_letter_path="",
        kyc_verified=None,
        current_step=WorkflowSteps.UNDERWRITING,  # Skip user interaction
        error_message=None,
        customer_name=None,
        customer_phone=None,
        customer_address=None,
        credit_score=None,
        pre_approved_limit=None
    )
    
    # Execute workflow starting from underwriting
    try:
        # Run underwriting node directly
        underwriting_result = call_underwriting_node(initial_state)
        initial_state.update(underwriting_result)
        
        # Route based on underwriting decision
        next_step = route_after_underwriting(initial_state)
        
        if next_step == "generate_sanction_letter":
            sanction_result = call_generate_sanction_letter_node(initial_state)
            initial_state.update(sanction_result)
        elif next_step == "handle_rejection":
            rejection_result = prepare_rejection_node(initial_state)
            initial_state.update(rejection_result)
        
        return initial_state
        
    except Exception as e:
        initial_state["error_message"] = f"Workflow execution error: {str(e)}"
        initial_state["current_step"] = WorkflowSteps.ERROR
        return initial_state