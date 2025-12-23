# Claverica Crypto Backend

Cryptocurrency and Fiat Management System

## Setup

1. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your DATABASE_URL
```

4. Seed database:
```bash
python seed_data.py
```

5. Run application:
```bash
uvicorn main:app --reload
```

API Docs: http://localhost:8000/docs

## API Endpoints

- GET  /api/crypto/assets - Get all crypto assets
- GET  /api/crypto/wallets/{user_id} - Get user wallets
- POST /api/crypto/wallets/create - Create new wallet
- GET  /api/crypto/transactions/{user_id} - Get transactions
- POST /api/crypto/transactions/create - Create transaction
- GET  /api/crypto/fiat-platforms - Get fiat platforms
- POST /api/crypto/fiat-accounts/create - Link fiat account
- GET  /api/crypto/fiat-accounts/{user_id} - Get fiat accounts

## Deployment to Render

1. Create PostgreSQL database
2. Create Web Service
3. Set environment variable: DATABASE_URL
4. Deploy!


===============================================================================
                            FILE STRUCTURE
===============================================================================

crypto-backend/
├── main.py                 # FastAPI application
├── database.py            # Database configuration
├── crypto_models.py       # SQLAlchemy models
├── crypto_routes.py       # API routes
├── seed_data.py           # Database seeding
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .gitignore            # Git ignore
└── README.md             # Documentation

===============================================================================
                         DEPLOYMENT STEPS
===============================================================================

1. Copy all files above to your backend folder
2. pip install -r requirements.txt
3. Create .env with your DATABASE_URL
4. python seed_data.py (to populate initial data)
5. uvicorn main:app --reload

===============================================================================
