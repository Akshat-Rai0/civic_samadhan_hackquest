# Auto Grievance Raiser (Nagar Seva)

A civic grievance redressal web application. It connects citizens reporting municipal issues with municipal staff who triage, assign, and resolve them.

This application is a prototype. Identity verification uses a simulated Aadhaar-style login with a test code rather than real UIDAI eKYC. There is no external AI chat integration or MCP server in this version. The four internal agents (classification, communication, escalation, verification) run as backend services and scheduled tasks.

## System Architecture

The project has two connected parts:

1. Citizen Portal
- Login: Mock identity login using name and 12-digit number.
- Photo intake: Captures civic issue photo with optional description. Geotagging is extracted on the server from image EXIF or device GPS.
- Detection preview: Moondream vision model detects municipal defects.
- Confirmation: Citizen reviews detected issues and confirms submission before routing.
- Status tracking: Step-by-step progress tracking, communication agent updates, and resolution verification confirmation.

2. Municipal Admin Dashboard
- Queue: Clustered issues sorted by computed priority score. Includes affected report counts, days pending, SLA status, and officer assignment.
- Spatial Heatmap: Interactive map displaying complaint density across wards and coordinates.
- Issue Dossier: Detailed issue view with photos, officer assignment dropdown, contractor dispatching, and resolution verification evidence.

3. Internal Backend Agents
- Classification Agent: Merges vision captions and descriptions, classifies category, extracts geotags, and routes to the appropriate municipal department.
- Communication Agent: Automatically creates notification entries whenever a ticket status changes.
- Escalation Agent: Watches SLA deadlines against severity guidelines and logs escalations to higher department tiers.
- Verification Agent: Analyzes completion photos submitted by field workers, runs automated checks, and prompts citizens to confirm resolution before closing.

## Color Scheme and Design Theme

- White: `#FFFFFF`
- Off-white page background: `#FAFAF7`
- Orange (primary accent, actions): `#F2994A`
- Green (success, resolved status): `#27A567`
- Blue (links, informational, status): `#2F80ED`
- Dark Orange (escalated status): `#D4722A`
- Neutral text: `#2B2B2B`
- Muted text: `#6B6B6B`
- Borders: `#E4E1D8`

## Quick Start (One Command)

To start both backend and frontend servers in one command:

```bash
./start.sh
```

Or from inside `grievance-app/`:

```bash
./grievance-app/start.sh
```

This checks virtual environment setup, copies `.env` if missing, installs dependencies if needed, and launches both services:
- Citizen Portal & Admin: http://localhost:5173
- Backend API Docs: http://localhost:8000/docs

## Backend Setup

1. Navigate to the backend directory:
```bash
cd grievance-app/backend
```

2. Create and activate a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
```

5. Start the FastAPI server:
```bash
uvicorn app.main:app --reload --port 8000
```

The API will be available at http://localhost:8000. Interactive documentation is at http://localhost:8000/docs.

6. (Optional) Run Celery worker and beat scheduler for background tasks:
```bash
celery -A app.tasks.celery_app worker --loglevel=info
celery -A app.tasks.celery_app beat --loglevel=info
```

## Frontend Setup

1. Navigate to the frontend directory:
```bash
cd grievance-app/frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

The application will run at http://localhost:5173.
