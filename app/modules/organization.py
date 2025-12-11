from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import Session, relationship, backref
from app.database import Base, get_db
# Import User for querying (not for relationship definition to avoid circular import issues)
from app.modules.auth import User 
from pydantic import BaseModel
from typing import Optional
import sys
import traceback

router = APIRouter(tags=["Organization"])

# --- ASSOCIATION TABLE (The Link) ---
# This table maps User IDs to Team IDs.
user_teams = Table(
    'user_teams', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('team_id', Integer, ForeignKey('teams.id'))
)

# --- Database Model ---
class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    
    # Hierarchy
    children = relationship(
        "Team", 
        backref=backref("parent", remote_side=[id]), 
        lazy="selectin"
    )

    # MANY-TO-MANY Relationship
    # This magic 'secondary' parameter tells SQLAlchemy to use the link table.
    members = relationship("User", secondary=user_teams, backref="teams", lazy="selectin")

# --- Input Schemas ---
class TeamCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

class MemberAction(BaseModel):
    username: str
    team_id: int

# --- Manual Serializer ---
def team_to_dict(team):
    children_list = team.children or []
    members_list = team.members or []
    return {
        "id": team.id,
        "name": team.name,
        "parent_id": team.parent_id,
        "members": [u.username for u in members_list],
        "children": [team_to_dict(child) for child in children_list]
    }

# --- Routes ---

@router.post("/teams/")
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    try:
        if team.parent_id is not None:
            if team.parent_id <= 0: raise HTTPException(status_code=400, detail="Invalid ID")
            if not db.query(Team).filter(Team.id == team.parent_id).first():
                raise HTTPException(status_code=404, detail="Parent not found")
        new_team = Team(name=team.name, parent_id=team.parent_id)
        db.add(new_team)
        db.commit()
        db.refresh(new_team)
        return JSONResponse(content={"id": new_team.id, "name": new_team.name, "status": "Created"})
    except Exception as e:
        db.rollback()
        raise e

@router.get("/hierarchy/")
def get_hierarchy(db: Session = Depends(get_db)):
    try:
        roots = db.query(Team).filter(Team.parent_id == None).all()
        data = [team_to_dict(root) for root in roots]
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

# --- MEMBER MANAGEMENT (Many-to-Many Logic) ---

@router.post("/members/add")
def add_member(action: MemberAction, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == action.username).first()
    team = db.query(Team).filter(Team.id == action.team_id).first()
    
    if not user or not team:
        raise HTTPException(status_code=404, detail="User or Team not found")

    # Check if already in team
    if user in team.members:
        return {"message": f"User {user.username} is already in {team.name}"}

    # Add to list (SQLAlchemy handles the link table automatically)
    team.members.append(user)
    db.commit()
    return {"message": f"User {user.username} added to {team.name}"}

@router.post("/members/remove")
def remove_member(action: MemberAction, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == action.username).first()
    team = db.query(Team).filter(Team.id == action.team_id).first()

    if not user or not team:
        raise HTTPException(status_code=404, detail="User or Team not found")

    if user not in team.members:
        raise HTTPException(status_code=400, detail="User is not in this team")

    # Remove from list
    team.members.remove(user)
    db.commit()
    return {"message": f"User {user.username} removed from {team.name}"}