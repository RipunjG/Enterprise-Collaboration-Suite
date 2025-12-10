from fastapi import FastAPI
from app.database import engine, Base
from app.modules import auth, organization  # <--- Import organization

# Create tables (Now includes 'teams' table)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Enterprise Suite - Step 3 (Hierarchy)")

app.include_router(auth.router, prefix="/auth")
app.include_router(organization.router, prefix="/org")  # <--- Add this line

@app.get("/")
def read_root():
    return {"status": "System Operational"}