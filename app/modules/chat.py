from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, or_, and_
from sqlalchemy.orm import Session, relationship
from app.database import Base, get_db, SessionLocal
from app.modules.auth import User
from app.modules.organization import Team
from datetime import datetime
import json
import sys

router = APIRouter(tags=["Chat"])

# --- Database Model ---
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    sender_id = Column(Integer, ForeignKey("users.id"))
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=True) # For DMs
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)      # For Teams
    
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])

# --- Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket
        print(f"✅ CONNECTION: {username} connected. Active users: {list(self.active_connections.keys())}")

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]
        print(f"❌ DISCONNECTION: {username} left.")

    async def send_personal_message(self, message: str, username: str):
        if username in self.active_connections:
            try:
                await self.active_connections[username].send_text(message)
                print(f"📨 SENT to {username}: {message}")
            except Exception as e:
                print(f"⚠️ SEND ERROR to {username}: {e}")
        else:
            print(f"⚠️ SKIP: {username} is offline.")

manager = ConnectionManager()

# --- Logic: Handle Routing & Persistence ---
async def handle_message(data: dict, sender_username: str, db: Session):
    print(f"📩 RECEIVED from {sender_username}: {data}")
    
    sender = db.query(User).filter(User.username == sender_username).first()
    if not sender:
        print("⛔ Sender not found in DB")
        return

    msg_type = data.get("type") # "dm" or "team"
    content = data.get("msg")
    
    # 1. DIRECT MESSAGE
    if msg_type == "dm":
        recipient_username = data.get("to")
        recipient = db.query(User).filter(User.username == recipient_username).first()
        
        if recipient:
            # A. Save to DB (History)
            new_msg = Message(content=content, sender_id=sender.id, recipient_id=recipient.id)
            db.add(new_msg)
            db.commit()
            print(f"💾 SAVED DM: {sender_username} -> {recipient_username}")

            # B. Send to Recipient (if online)
            payload = json.dumps({
                "type": "dm",
                "from": sender_username, 
                "msg": content,
                "timestamp": str(new_msg.timestamp)
            })
            await manager.send_personal_message(payload, recipient_username)
        else:
            print(f"⛔ Recipient '{recipient_username}' does not exist.")

    # 2. TEAM MESSAGE
    elif msg_type == "team":
        team_id = data.get("team_id")
        team = db.query(Team).filter(Team.id == team_id).first()
        
        if team:
            # A. Save to DB
            new_msg = Message(content=content, sender_id=sender.id, team_id=team.id)
            db.add(new_msg)
            db.commit()
            print(f"💾 SAVED TEAM MSG: {sender_username} -> Team {team.name}")

            # B. Broadcast to Team Members
            payload = json.dumps({
                "type": "team",
                "team": team.name, 
                "from": sender_username, 
                "msg": content,
                "timestamp": str(new_msg.timestamp)
            })
            
            for member in team.members:
                # Don't echo back to sender via WebSocket (they know what they sent)
                if member.username != sender_username:
                    await manager.send_personal_message(payload, member.username)
        else:
            print(f"⛔ Team ID {team_id} not found.")

# --- Routes ---

@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    db = SessionLocal()
    try:
        while True:
            text_data = await websocket.receive_text()
            try:
                data = json.loads(text_data)
                await handle_message(data, username, db)
            except json.JSONDecodeError:
                print("⚠️ Invalid JSON received")
    except WebSocketDisconnect:
        manager.disconnect(username)
    finally:
        db.close()

# --- History Endpoints ---

@router.get("/history/dm/{other_user}")
def get_dm_history(other_user: str, my_username: str, db: Session = Depends(get_db)):
    # Find IDs
    me = db.query(User).filter(User.username == my_username).first()
    other = db.query(User).filter(User.username == other_user).first()
    
    if not me or not other:
        return []

    # Fetch conversation between Me and Other
    msgs = db.query(Message).filter(
        or_(
            and_(Message.sender_id == me.id, Message.recipient_id == other.id),
            and_(Message.sender_id == other.id, Message.recipient_id == me.id)
        )
    ).order_by(Message.timestamp.asc()).all()

    # Format for Frontend
    return [{"from": m.sender.username, "msg": m.content, "timestamp": str(m.timestamp)} for m in msgs]

@router.get("/history/team/{team_id}")
def get_team_history(team_id: int, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(Message.team_id == team_id).order_by(Message.timestamp.asc()).all()
    return [{"from": m.sender.username, "msg": m.content, "timestamp": str(m.timestamp)} for m in msgs]