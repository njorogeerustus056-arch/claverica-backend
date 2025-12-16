
# ============================================================================
# FILE 9: README.md
# ============================================================================

"""
# Claverica Compliance API

KYC and Compliance Management System for Claverica Foreign Exchange Platform

## Features

- KYC Verification System
- Document Upload & Management
- TAC (Transfer Authorization Code) Generation & Verification
- Withdrawal Request Management
- Compliance Audit Logging
- Email Notifications

## Tech Stack

- FastAPI
- PostgreSQL (via Render)
- SQLAlchemy ORM
- Pydantic for validation

## Setup Instructions

### 1. Clone Repository

```bash
git clone <your-repo-url>
cd compliance-backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` with your actual credentials:
- Add your Render PostgreSQL DATABASE_URL
- Configure SMTP settings for emails
- Set security keys

### 5. Run Migrations

```bash
# Database tables will be created automatically on first run
python main.py
```

### 6. Run the Application

```bash
uvicorn main:app --reload
```

The API will be available at: `http://localhost:8000`

API Documentation: `http://localhost:8000/docs`

## Deployment to Render

### 1. Create PostgreSQL Database

1. Go to Render Dashboard
2. Click "New +" → "PostgreSQL"
3. Configure and create database
4. Copy the Internal Database URL

### 2. Create Web Service

1. Click "New +" → "Web Service"
2. Connect your repository
3. Configure:
   - **Name**: claverica-compliance-api
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 3. Add Environment Variables

In Render dashboard, add:
- `DATABASE_URL`: (from your PostgreSQL database)
- `SMTP_HOST`: smtp.gmail.com
- `SMTP_PORT`: 587
- `SMTP_USER`: your-email@gmail.com
- `SMTP_PASSWORD`: your-app-password
- `FROM_EMAIL`: noreply@claverica.com
- `SECRET_KEY`: (generate a secure random string)

### 4. Deploy

Click "Create Web Service" and wait for deployment to complete.

## API Endpoints

### KYC Management

- `POST /api/compliance/kyc/submit` - Submit KYC verification
- `GET /api/compliance/kyc/status/{user_id}` - Get KYC status
- `POST /api/compliance/kyc/upload-document` - Upload KYC document
- `GET /api/compliance/verification/documents/{verification_id}` - Get documents

### TAC Management

- `POST /api/compliance/tac/generate` - Generate TAC code
- `POST /api/compliance/tac/verify` - Verify TAC code

### Withdrawal Management

- `POST /api/compliance/withdrawal/request` - Request withdrawal

### Audit

- `GET /api/compliance/audit-log/{user_id}` - Get audit logs

## File Structure

```
compliance-backend/
├── main.py                 # FastAPI application
├── database.py            # Database configuration
├── compliance_models.py   # SQLAlchemy models
├── compliance_routes.py   # API routes
├── email_service.py       # Email utilities
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore rules
├── README.md             # This file
└── uploads/              # File uploads directory
    └── kyc/              # KYC documents
```

## Security Notes

- Never commit `.env` file
- Change SECRET_KEY in production
- Use strong passwords for database
- Enable HTTPS in production
- Implement rate limiting for TAC endpoints
- Regular security audits

## Support

For issues or questions, contact: support@claverica.com
"""
