from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base, SessionLocal
from app.modules import auth, organization, chat
from app.modules.auth import User, get_password_hash
from app.modules.organization import Team

# 1. Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Enterprise Suite")

# 2. ENABLE CORS (Fixes the "Can't load history" issue)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (files, localhost, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(organization.router, prefix="/org")
app.include_router(chat.router, prefix="/chat")

# 3. AUTO-CREATE DATA (Fixes the "User not found" issue)
@app.on_event("startup")
def startup_populate_db():
    db = SessionLocal()
    try:
        # Create Alice
        if not db.query(User).filter(User.username == "alice").first():
            alice = User(username="alice", hashed_password=get_password_hash("123"))
            db.add(alice)
            print("✅ Created User: alice")

        # Create Bob
        if not db.query(User).filter(User.username == "bob").first():
            bob = User(username="bob", hashed_password=get_password_hash("123"))
            db.add(bob)
            print("✅ Created User: bob")
        
        # Create Team
        if not db.query(Team).filter(Team.name == "Engineering").first():
            team = Team(name="Engineering", parent_id=None)
            db.add(team)
            db.commit() # Commit to get the ID
            
            # Add Alice and Bob to Team
            # We need to re-fetch users to attach them
            alice = db.query(User).filter(User.username == "alice").first()
            bob = db.query(User).filter(User.username == "bob").first()
            team.members.append(alice)
            team.members.append(bob)
            print(f"✅ Created Team: Engineering (ID: {team.id}) with Alice & Bob")
        
        db.commit()
    except Exception as e:
        print(f"Startup Error: {e}")
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "System Operational"}