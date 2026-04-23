# 🛡️ ResolveMesh: AI-Powered Dispute Resolution & Privacy Shield
#### ResolveMesh is a professional-grade dispute management system designed to streamline customer claims while maintaining strict data privacy compliance (PDPA). It utilizes a multi-layered agentic AI approach to redact sensitive PII, detect fraudulent "double-dipping," and cross-reference claims against a digital twin bank ledger.

## 🛠️ Project Structure
Plaintext
ResolveMesh/

├── backend/            # FastAPI + Python (Privacy Shield & Logic)

├── frontend/           # React + Lovable (Dashboard & Ingest)

├── API_CONTRACT.md     # Documentation for endpoint JSON formats

└── .env.example        # Template for API keys

## ⚙️ Setup Instructions
1. Prerequisites
- Python 3.10+
- Node.js 18+
- Supabase Account

2. Backend Setup (FastAPI)
The backend manages the security layer and database orchestration.

```Bash
# Navigate to backend
cd backend

# Create and activate virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download the Malaysian-context NLP model (Required)
python -m spacy download en_core_web_sm

# Start the server
uvicorn main:app --reload
The API will be live at http://localhost:8000. Access Swagger UI at http://localhost:8000/docs.
```

3. Frontend Setup (React/Vite)
The frontend provides the "Sleuth" dashboard and customer ingest portal.

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
