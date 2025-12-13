from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, or_, and_
from sqlalchemy.orm import Session, relationship
from app.database import Base, get_db, SessionLocal
from app.modules.auth import User
from app.modules.organization import Team
from datetime import datetime
import json

router = APIRouter(tags=["Chat"])

# --- Database Model (Fixed with CASCADE) ---
class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # FIX: Add ondelete="CASCADE"
    # If User or Team is deleted, these messages vanish automatically.
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"), nullable=True)
    
    sender = relationship("User", foreign_keys=[sender_id])
    recipient = relationship("User", foreign_keys=[recipient_id])
    team = relationship("Team", foreign_keys=[team_id])

# --- Connection Manager (Fixed for Zombie Connections) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]

    async def send_personal_message(self, message: str, username: str):
        if username in self.active_connections:
            try:
                await self.active_connections[username].send_text(message)
            except RuntimeError:
                # Socket is dead, remove it to stop errors
                self.disconnect(username)
            except Exception as e:
                print(f"⚠️ Error sending to {username}: {e}")

manager = ConnectionManager()

# --- Logic: Handle Message ---
async def handle_message(data: dict, sender_username: str, db: Session):
    sender = db.query(User).filter(User.username == sender_username).first()
    if not sender: return

    msg_type = data.get("type")
    content = data.get("msg")
    
    if msg_type == "dm":
        recipient_username = data.get("to")
        recipient = db.query(User).filter(User.username == recipient_username).first()
        
        if recipient:
            new_msg = Message(content=content, sender_id=sender.id, recipient_id=recipient.id)
            db.add(new_msg)
            db.commit()

            payload = json.dumps({
                "type": "dm", "from": sender_username, "to": recipient_username,
                "msg": content, "timestamp": str(new_msg.timestamp)
            })
            await manager.send_personal_message(payload, recipient_username)
            # Echo back to sender so they see it too (if using multiple tabs)
            await manager.send_personal_message(payload, sender_username)

    elif msg_type == "team":
        team = None
        if "team_id" in data:
            team = db.query(Team).filter(Team.id == data["team_id"]).first()
        
        if team:
            if sender not in team.members: return 

            new_msg = Message(content=content, sender_id=sender.id, team_id=team.id)
            db.add(new_msg)
            db.commit()

            payload = json.dumps({
                "type": "team", "team": team.name, "team_id": team.id,
                "from": sender_username, "msg": content, "timestamp": str(new_msg.timestamp)
            })
            
            for member in team.members:
                await manager.send_personal_message(payload, member.username)

# --- Routes ---

@router.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    await manager.connect(websocket, username)
    db = SessionLocal()
    try:
        while True:
            text_data = await websocket.receive_text()
            data = json.loads(text_data)
            await handle_message(data, username, db)
    except WebSocketDisconnect:
        manager.disconnect(username)
    except Exception:
        manager.disconnect(username)
    finally:
        db.close()

@router.get("/sidebar/{username}")
def get_sidebar_data(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user: return []

    sidebar_items = []

    # 1. Teams
    for team in user.teams:
        last_msg = db.query(Message).filter(Message.team_id == team.id)\
                     .order_by(Message.timestamp.desc()).first()
        sidebar_items.append({
            "type": "team", "name": team.name, "id": team.id,
            "last_msg": last_msg.content[:30] if last_msg else "",
            "timestamp": str(last_msg.timestamp) if last_msg else ""
        })

    # 2. DMs (Unique people)
    dm_msgs = db.query(Message).filter(
        or_(Message.sender_id == user.id, Message.recipient_id == user.id),
        Message.team_id == None
    ).order_by(Message.timestamp.desc()).all()

    seen_people = set()
    for msg in dm_msgs:
        other = msg.recipient if msg.sender_id == user.id else msg.sender
        if other and other.username not in seen_people:
            seen_people.add(other.username)
            sidebar_items.append({
                "type": "dm", "name": other.username, "id": other.id,
                "last_msg": msg.content[:30],
                "timestamp": str(msg.timestamp)
            })
    
    # Sort sidebar by newest message
    # FIX: Handle empty timestamps safely
    sidebar_items.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    return sidebar_items

# --- History Endpoints ---
@router.get("/history/dm/{other_user}")
def get_dm_history(other_user: str, my_username: str, db: Session = Depends(get_db)):
    me = db.query(User).filter(User.username == my_username).first()
    other = db.query(User).filter(User.username == other_user).first()
    if not me or not other: return []
    
    msgs = db.query(Message).filter(
        or_(
            and_(Message.sender_id == me.id, Message.recipient_id == other.id),
            and_(Message.sender_id == other.id, Message.recipient_id == me.id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    return [{"from": m.sender.username, "msg": m.content, "timestamp": str(m.timestamp)} for m in msgs]

@router.get("/history/team/{team_id}")
def get_team_history(team_id: int, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(Message.team_id == team_id).order_by(Message.timestamp.asc()).all()
    return [{"from": m.sender.username, "msg": m.content, "timestamp": str(m.timestamp)} for m in msgs]