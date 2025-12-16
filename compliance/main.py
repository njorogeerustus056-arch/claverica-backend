from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from database import init_db
from compliance_routes import router as compliance_router

# Create uploads directory
os.makedirs("uploads/kyc", exist_ok=True)

app = FastAPI(
    title="Claverica Compliance API",
    description="KYC and Compliance Management System",
    version="1.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-frontend-domain.com"  # Add your actual frontend domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for uploads
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Include routers
app.include_router(compliance_router)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("✅ Database initialized successfully")
    print("✅ Compliance API is running")

@app.get("/")
async def root():
    return {
        "message": "Claverica Compliance API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "kyc_submit": "/api/compliance/kyc/submit",
            "kyc_status": "/api/compliance/kyc/status/{user_id}",
            "upload_document": "/api/compliance/kyc/upload-document",
            "tac_generate": "/api/compliance/tac/generate",
            "tac_verify": "/api/compliance/tac/verify",
            "withdrawal_request": "/api/compliance/withdrawal/request",
            "verification_documents": "/api/compliance/verification/documents/{verification_id}",
            "audit_log": "/api/compliance/audit-log/{user_id}"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )

