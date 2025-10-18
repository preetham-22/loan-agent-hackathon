# AI-Powered Loan Agent System 🏦🤖

An intelligent loan processing system built with AI agents, FastAPI, and Streamlit that automates the entire loan application workflow from natural language processing to document generation.

## 🌟 Features

- **Natural Language Processing**: Chat interface for loan applications
- **Intelligent Underwriting**: AI-powered loan evaluation and approval
- **KYC Verification**: Automated Know Your Customer checks
- **Credit Assessment**: Real-time credit score evaluation
- **Document Generation**: Professional PDF sanction letters
- **Mock Banking APIs**: Simulated banking services for testing

## 🏗️ Architecture

```
loan_agent_hackathon/
├── agents/
│   ├── tools.py        # Core business logic tools
│   └── graph.py        # LangGraph workflow orchestration
├── mock_server/
│   ├── api.py          # FastAPI backend services
│   └── dummy_data.json # Sample customer data
├── app/
│   └── main.py         # Streamlit frontend interface
├── output/             # Generated documents
├── requirements.txt    # Python dependencies
└── .env               # Environment variables (not tracked)
```

## 🛠️ Technologies Used

- **Backend**: FastAPI, Uvicorn
- **AI Framework**: LangGraph, LangChain
- **LLM**: OpenAI GPT models with structured output
- **Frontend**: Streamlit
- **Document Generation**: ReportLab
- **Data Validation**: Pydantic
- **HTTP Client**: Requests

## 🚀 Quick Start

### Prerequisites

- Python 3.13+
- OpenAI API key
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd loan_agent_hackathon
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key_here
   ```

### Running the Application

1. **Start the FastAPI backend** (Terminal 1)
   ```bash
   uvicorn mock_server.api:app --reload
   ```
   The API will be available at `http://127.0.0.1:8000`

2. **Start the Streamlit frontend** (Terminal 2)
   ```bash
   streamlit run app/main.py
   ```
   The interface will be available at `http://localhost:8501`

## 📖 Usage

1. **Access the chat interface** at `http://localhost:8501`
2. **Start a conversation** with the loan agent
3. **Provide loan requirements** in natural language
4. **Upload salary slip** (optional) for income verification
5. **Receive instant loan approval** with generated sanction letter

### Example Interactions

```
User: "I need a loan of 500000 for home purchase"
Agent: I'll help you process your loan application...

User: "My customer ID is CUST001 and I need 75000 for business"
Agent: Let me verify your details and process your application...
```

## 🔧 API Endpoints

The mock server provides the following endpoints:

- `GET /` - Health check
- `GET /kyc/{customer_id}` - KYC verification
- `GET /credit-score/{customer_id}` - Credit score retrieval
- `GET /pre-approved-limit/{customer_id}` - Pre-approved loan limit
- `POST /upload-salary-slip` - Salary slip upload

## 🧠 AI Workflow

The system uses LangGraph to orchestrate the following workflow:

1. **Query Processing**: Extract loan requirements from natural language
2. **KYC Verification**: Validate customer identity and eligibility
3. **Credit Assessment**: Evaluate creditworthiness and risk
4. **Underwriting Decision**: Make intelligent loan approval decisions
5. **Document Generation**: Create professional sanction letters

## 📊 Sample Data

The system includes 10 synthetic customer profiles for testing:
- Customer IDs: CUST001 to CUST010
- Varied credit scores and financial profiles
- Different risk categories and loan limits

## 🔐 Security Features

- Environment variables for sensitive data
- `.gitignore` protection for API keys
- Input validation with Pydantic models
- Structured output parsing for reliability

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing powerful language models
- LangChain team for the excellent AI framework
- FastAPI and Streamlit communities for amazing tools

## 📞 Support

For questions and support, please open an issue on GitHub or contact the development team.

---

**Note**: This is a demonstration system with mock data. For production use, integrate with real banking APIs and implement proper security measures.