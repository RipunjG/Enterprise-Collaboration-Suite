from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import Session, relationship, backref
from app.database import Base, get_db
from app.modules.auth import User 
from pydantic import BaseModel
from typing import Optional
import sys
import traceback

router = APIRouter(tags=["Organization"])

# --- ASSOCIATION TABLE ---
user_teams = Table(
    'user_teams', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('team_id', Integer, ForeignKey('teams.id'))
)

# --- MODELS ---
class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    
    # CASCADE DELETE: If parent is deleted, delete children automatically
    children = relationship(
        "Team", 
        backref=backref("parent", remote_side=[id]), 
        lazy="selectin",
        cascade="all, delete" 
    )
    members = relationship("User", secondary=user_teams, backref="teams", lazy="selectin")

# --- SCHEMAS ---
class TeamCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

class MemberAction(BaseModel):
    username: str
    team_id: int

# --- HELPER ---
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

# --- ROUTES ---

@router.get("/hierarchy/")
def get_hierarchy(db: Session = Depends(get_db)):
    try:
        roots = db.query(Team).filter(Team.parent_id == None).all()
        data = [team_to_dict(root) for root in roots]
        return JSONResponse(content=data)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

@router.post("/teams/")
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    try:
        new_team = Team(name=team.name, parent_id=team.parent_id)
        db.add(new_team)
        db.commit()
        db.refresh(new_team)
        return JSONResponse(content={"id": new_team.id, "name": new_team.name, "status": "Created"})
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# --- NEW: Delete Endpoint ---
@router.delete("/teams/{team_id}")
def delete_team(team_id: int, db: Session = Depends(get_db)):
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Because of cascade="all, delete", this deletes sub-teams too
    db.delete(team)
    db.commit()
    return {"message": f"Team {team_id} and its children deleted"}

@router.post("/members/add")
def add_member(action: MemberAction, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == action.username).first()
    team = db.query(Team).filter(Team.id == action.team_id).first()
    
    if not user: raise HTTPException(404, "User not found")
    if not team: raise HTTPException(404, "Team not found")

    if user not in team.members:
        team.members.append(user)
        db.commit()
    return {"message": "Added"}

@router.post("/members/remove")
def remove_member(action: MemberAction, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == action.username).first()
    team = db.query(Team).filter(Team.id == action.team_id).first()
    
    if not user or not team: raise HTTPException(404, "Not found")

    if user in team.members:
        team.members.remove(user)
        db.commit()
    return {"message": "Removed"}