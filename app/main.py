import streamlit as st
import uuid
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import the main agent, with fallback
try:
    from agents.graph import app, AgentState
    AGENT_AVAILABLE = True
except ImportError as e:
    st.warning("⚠️ Running in Demo Mode - Full AI agent not available")
    print(f"Agent import failed: {e}")
    from agents.simple_agent import process_loan_application
    AGENT_AVAILABLE = False
    AgentState = dict  # Simple fallback

# Page configuration
st.set_page_config(
    page_title="Tata Capital - AI Loan Assistant",
    page_icon="🏦",
    layout="wide"
)

# Title and Initial Setup
st.title("🏦 Tata Capital - AI Loan Assistant")
st.markdown("---")

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "needs_salary_slip" not in st.session_state:
    st.session_state.needs_salary_slip = False

# Display welcome message if no messages exist
if not st.session_state.messages:
    with st.chat_message("assistant"):
        st.write("👋 Welcome to Tata Capital! I'm your AI Loan Assistant. I can help you process your loan application.")
        st.write("To get started, please tell me your customer ID and the loan amount you're looking for.")
        st.write("For example: *'I need a loan of ₹50,000 for customer ID 5'*")

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# Handle User Input
if prompt := st.chat_input("How can I help you today?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Create input for LangGraph app
    graph_input = AgentState(
        customer_id=0,  # Will be extracted by the agent
        requested_amount=0.0,  # Will be extracted by the agent
        monthly_salary=0.0,
        messages=st.session_state.messages.copy(),
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
    
    # Generate and stream assistant response
    with st.chat_message("assistant"):
        try:
            # Simple direct execution (better for debugging)
            with st.spinner("Processing your loan application..."):
                # Execute the workflow with fallback support
                if AGENT_AVAILABLE:
                    final_state = app.invoke(graph_input)
                    
                    # Extract the response from final state
                    full_response = "I'm processing your request..."
                    
                    if final_state and "messages" in final_state:
                        messages = final_state["messages"]
                        if messages:
                            # Find the last assistant message
                            for message in reversed(messages):
                                if message.get("role") == "assistant":
                                    full_response = message.get("content", "Processing complete.")
                                    break
                else:
                    # Use simple fallback processing
                    full_response = process_loan_application(prompt)
                
                # Display the response
                st.write(full_response)
            
            # Add assistant response to chat history
            if full_response and full_response != "I'm processing your request...":
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
                # Check if we need salary slip information
                if "salary slip" in full_response.lower():
                    st.session_state.needs_salary_slip = True
            
        except Exception as e:
            error_message = f"I apologize, but I encountered an error while processing your request: {str(e)}"
            st.error(error_message)
            st.session_state.messages.append({"role": "assistant", "content": error_message})

# Handle Salary Slip Edge Case
if st.session_state.get("needs_salary_slip", False):
    st.markdown("---")
    st.subheader("📄 Additional Information Required")
    
    with st.form("salary_form"):
        st.write("To proceed with your loan application, please provide your salary information:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            salary = st.number_input(
                "Please enter your monthly salary (₹):",
                min_value=0.0,
                step=1000.0,
                format="%.2f"
            )
        
        with col2:
            salary_slip_file = st.file_uploader(
                "Upload your salary slip:",
                type=['pdf', 'jpg', 'jpeg', 'png'],
                help="Upload a PDF or image file of your salary slip"
            )
        
        submitted = st.form_submit_button("Submit Salary Information", type="primary")
        
        if submitted:
            if salary > 0:
                # Create structured message with salary information
                salary_message = f"My monthly salary is ₹{salary:,.2f}"
                if salary_slip_file:
                    salary_message += f" and I have uploaded my salary slip ({salary_slip_file.name})."
                else:
                    salary_message += " (salary slip document uploaded)."
                
                # Add the salary information as a new user message
                st.session_state.messages.append({"role": "user", "content": salary_message})
                
                # Reset the salary slip flag
                st.session_state.needs_salary_slip = False
                
                # Rerun the app to trigger the agent with new information
                st.rerun()
            else:
                st.error("Please enter a valid salary amount.")

# Sidebar with additional information
with st.sidebar:
    st.header("ℹ️ How it Works")
    st.markdown("""
    **Step 1:** Tell me your customer ID and desired loan amount
    
    **Step 2:** I'll verify your KYC details and check your eligibility
    
    **Step 3:** If needed, I may ask for additional documentation
    
    **Step 4:** You'll receive instant approval/rejection with detailed reasoning
    
    **Step 5:** Approved loans get an instant sanction letter
    """)
    
    st.markdown("---")
    
    st.header("📞 Need Help?")
    st.markdown("""
    **Sample Request:**
    - "I need a loan of ₹75,000 for customer ID 3"
    - "Customer 7 wants to apply for ₹40,000"
    - "Apply for ₹60,000 loan, customer ID 1"
    """)
    
    st.markdown("---")
    
    st.header("🏦 Customer IDs Available")
    st.markdown("""
    **Test with these customer IDs:**
    - Customer 1-10 (demo data available)
    - Each has different credit profiles
    - Various approval scenarios
    """)
    
    if st.session_state.messages:
        if st.button("🔄 Start New Conversation"):
            st.session_state.messages = []
            st.session_state.needs_salary_slip = False
            st.session_state.session_id = str(uuid.uuid4())
            st.rerun()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "🤖 Powered by AI • Built with LangGraph & Streamlit • Tata Capital Demo"
    "</div>", 
    unsafe_allow_html=True
)