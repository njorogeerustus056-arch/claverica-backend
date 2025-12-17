from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from database import init_db
from crypto_routes import router as crypto_router

app = FastAPI(
    title="Claverica Crypto API",
    description="Cryptocurrency & Fiat Management System",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-frontend-domain.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(crypto_router)

@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Database initialized successfully")
    print("✅ Crypto API is running")

@app.get("/")
async def root():
    return {
        "message": "Claverica Crypto API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "assets": "/api/crypto/assets",
            "wallets": "/api/crypto/wallets/{user_id}",
            "transactions": "/api/crypto/transactions/{user_id}",
            "fiat_platforms": "/api/crypto/fiat-platforms",
            "fiat_accounts": "/api/crypto/fiat-accounts/{user_id}"
        }
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "connected"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )
