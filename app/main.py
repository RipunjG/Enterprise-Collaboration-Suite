from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.modules import auth, organization, chat

# 1. Initialize Tables
# This creates the empty tables (Users, Teams, Messages) if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Enterprise Suite")

# 2. CORS (Allow Frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 3. Register Routers
app.include_router(auth.router, prefix="/auth")
app.include_router(organization.router, prefix="/org")
app.include_router(chat.router, prefix="/chat")

@app.get("/")
def read_root():
    return {"status": "Enterprise System Operational"}