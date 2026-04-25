# 🛡️ ResolveMesh: AI-Powered Dispute Resolution & Privacy Shield

#### ResolveMesh is a professional-grade dispute management system designed to streamline customer claims while maintaining strict data privacy compliance (PDPA). It utilizes a multi-layered agentic AI approach to redact sensitive PII, detect fraudulent "double-dipping," and cross-reference claims against a digital twin bank ledger.

---

## 📺 Demo Video

> [Link to Demo Video] - _Watch ResolveMesh Pitching Video._

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

4. ngrok Tunneling Setup (Required for n8n Integration)

Since n8n Cloud needs to reach your local FastAPI backend, you need to expose it via ngrok:

```Bash
# In a new terminal window
ngrok http 8000
```

This will generate a public URL (e.g., `https://xxxxx.ngrok.io`). Use this URL in your n8n workflows to reach your backend endpoints.

Example: Instead of `http://localhost:8000/redact`, use `https://xxxxx.ngrok.io/redact` in your n8n nodes.

🔑 Environment Variables

Create a `.env` file in the root directory with the following configuration:

```plaintext
SUPABASE_URL=https://ztamcvkqxjucvaiziwqs.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
ZAI_API_KEY=your_zai_platform_key
PORT=8000
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_PASSWORD=your-gmail-app-password
```

**Note**: For `GMAIL_PASSWORD`, use a [Gmail App Password](https://myaccount.google.com/apppasswords), not your regular Gmail password.

## � n8n Integration & Trigger Nodes

ResolveMesh uses **n8n Cloud** automation to handle incoming disputes from multiple channels. Since n8n Cloud is an external service that needs to reach your local FastAPI backend, **ngrok is required** to expose the backend via a public URL.

Configure the following triggers in your n8n workflows:

### 1️⃣ IMAP Trigger (Email Intake)

**Purpose**: Listen for incoming complaint emails

- **Service**: IMAP (Gmail)
- **Email**: `unemployedsquad123@gmail.com`
- **Credentials**: Use the `GMAIL_ADDRESS` and `GMAIL_PASSWORD` from `.env`
- **Action**: Extracts email content and forwards to the backend `/redact` endpoint via your ngrok URL (e.g., `https://xxxxx.ngrok.io/redact`)

### 2️⃣ Webhook Trigger (Customer Portal)

**Purpose**: Accept complaint submissions from the web form

- **Webhook URL**: `https://unemployed.app.n8n.cloud/webhook-test/userComplaint`
- **Method**: POST
- **Payload**: Accepts form data with fields like `platform`, `account_id`, `transactionId`, `summary`, `details`, and file attachments
- **Action**: Forwards structured complaint data to the backend for processing via ngrok

**Important Note**: Replace `http://localhost:8000` with your ngrok public URL (obtained from step 4 of setup) in all n8n API calls to your backend endpoints.

Both triggers route to the backend's `/redact` endpoint, which initiates "The Guardian" agent to sanitize PII and create the initial case record in Supabase.

## �🛡️ Security & Governance

**Data Privacy**: Automatic PII redaction using Spacy & LLM "Guardian" agents.

**Row-Level Security (RLS)**: Database-native protection ensures staff only see authorized cases.

**Decision Support System (DSS)**: AI provides the reasoning; a human staff member triggers the final "Close Case" action.
