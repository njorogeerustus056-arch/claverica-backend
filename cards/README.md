# Cards Backend API

Backend service for the Cards Management System built with FastAPI and PostgreSQL.

## Features

- 🔐 JWT Authentication
- 💳 Card Management (Virtual & Physical)
- 👤 User Management
- 💰 Balance Tracking
- 🔒 Secure Password Hashing
- 📊 Transaction History
- 🚀 Ready for Render Deployment

## Setup

### Local Development

1. Clone the repository

2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create `.env` file:
   ```bash
   cp .env.example .env
   ```

5. Update `.env` with your database credentials

6. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at http://localhost:8000

### Render Deployment

1. Push code to GitHub
2. Connect repository to Render
3. Render will automatically detect `render.yaml`
4. Add environment variables in Render dashboard
5. Deploy!

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Users
- `GET /api/users/me` - Get current user
- `GET /api/users/balance` - Get user balance
- `POST /api/users/balance/add` - Add balance
- `GET /api/users/transactions` - Get transaction history

### Cards
- `POST /api/cards/` - Create new card
- `GET /api/cards/` - Get all user cards
- `GET /api/cards/{card_id}` - Get specific card
- `PATCH /api/cards/{card_id}` - Update card
- `DELETE /api/cards/{card_id}` - Delete card
- `POST /api/cards/{card_id}/freeze` - Freeze card
- `POST /api/cards/{card_id}/unfreeze` - Unfreeze card
- `POST /api/cards/{card_id}/top-up` - Top up card balance

## Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Technology Stack

- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL** - Database
- **Pydantic** - Data validation
- **JWT** - Authentication
- **Bcrypt** - Password hashing

## Project Structure

```
app/
├── __init__.py
├── main.py              # Application entry point
├── database.py          # Database configuration
├── models.py            # SQLAlchemy models
├── schemas.py           # Pydantic schemas
├── utils.py             # Utility functions
├── dependencies.py      # FastAPI dependencies
└── routers/
    ├── __init__.py
    ├── auth.py          # Authentication routes
    ├── users.py         # User routes
    └── cards.py         # Card routes
```

## Environment Variables

- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - JWT secret key
- `ALGORITHM` - JWT algorithm (HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration time

## Frontend Integration

Update your frontend API calls to point to your deployed backend:

```typescript
const API_BASE_URL = "https://your-app.onrender.com";

// Example: Login
const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ username, password }),
});

// Example: Get cards (authenticated)
const response = await fetch(`${API_BASE_URL}/api/cards/`, {
  headers: {
    "Authorization": `Bearer ${accessToken}`,
  },
});
```

## License

MIT License
```

---

## Quick Setup Instructions

1. Create a new folder called `cards-backend`
2. Copy each file above into the correct location
3. Install dependencies: `pip install -r requirements.txt`
4. Create `.env` file from `.env.example`
5. Run locally: `uvicorn app.main:app --reload`
6. For Render: Push to GitHub and connect to Render

## Testing the API

Once running locally, visit:
- http://localhost:8000/docs - Interactive API documentation
- http://localhost:8000/health - Health check endpoint
