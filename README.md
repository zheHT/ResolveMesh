# 🛡️ ResolveMesh: AI-Powered Dispute Resolution & Privacy Shield

#### ResolveMesh is a professional-grade dispute management system designed to streamline customer claims while maintaining strict data privacy compliance (PDPA). It utilizes a multi-layered agentic AI approach to redact sensitive PII, detect fraudulent "double-dipping," and cross-reference claims against a digital twin bank ledger.

---

## 📺 Demo Video
> [Link to Demo Video] - *Watch ResolveMesh Pitching Video.*

---

## 🏗️ System Architecture & Multi-Agent Logic
ResolveMesh moves beyond simple chatbots by utilizing **Stateful Decision Making**. Every dispute follows a strictly governed "Handshake" protocol:

1. **The Guardian (Ingestion)**: Actively listens to inputs, sanitizes PII using NLP, and initializes the case in Supabase.
2. **The Sleuth (Investigation)**: Autonomously fetches records from Bank Ledgers and Merchant Kitchen logs.
3. **The Judge (Arbitration)**: Weighs the evidence against company policy to provide a verdict.
4. **The Reporter (Documentation)**: Generates a human-readable forensic audit and a "Police-Friendly" redacted summary.

## 🛠️ Project Structure
```Plaintext
ResolveMesh/
├── Attachments/           # Sample documents to feed the AI Agents
├── ComplaintUI/           # Dummy Customer Service Portal
├── backend/               # FastAPI + Python + AI Agents (Privacy Shield & Logic)
├── frontend/              # React + Lovable (Dashboard & Ingest)
└── verdict-pdf-service/   # Microservice for tuning dispute investigation output
```

## ⚙️ Setup Instructions
1. Prerequisites
- Python 3.10+
- Node.js 18+
- Supabase Account & n8n Cloud Access

2. Backend Setup (FastAPI)
The backend manages the security layer and database orchestration.

```Bash
cd backend
python -m venv venv
# Activate venv:
# Windows: .\venv\Scripts\activate | Mac/Linux: source venv/bin/activate

pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn main:app --reload
```
The API will be live at http://localhost:8000. Access Swagger UI at http://localhost:8000/docs.


3. Frontend Setup (React/Vite)

```Bash
# In a new terminal window
cd frontend
npm install
npm run dev
```
The dashboard will be live at http://localhost:5173.

🔑 Environment Variables

Create a .env file in the backend directory and add the following keys:
```Plaintext
SUPABASE_URL=your_project_url
SUPABASE_SERVICE_KEY=your_service_role_key
ZAI_API_KEY=your_zai_platform_key
```

## 🛡️ Security & Governance
**Data Privacy**: Automatic PII redaction using Spacy & LLM "Guardian" agents.

**Row-Level Security (RLS)**: Database-native protection ensures staff only see authorized cases.

**Decision Support System (DSS)**: AI provides the reasoning; a human staff member triggers the final "Close Case" action.
