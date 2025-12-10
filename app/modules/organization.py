from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import Session, relationship, backref  # <--- Import backref
from app.database import Base, get_db
from pydantic import BaseModel
from typing import Optional
import sys
import traceback

router = APIRouter(tags=["Organization"])

# --- Database Model ---
class Team(Base):
    __tablename__ = "teams"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    parent_id = Column(Integer, ForeignKey('teams.id'), nullable=True)
    
    # --- THE FIX ---
    # remote_side=[id] MUST be inside the backref() function.
    # This tells SQLAlchemy: "The 'parent' property points to the ID column."
    children = relationship(
        "Team", 
        backref=backref("parent", remote_side=[id]), 
        lazy="selectin"
    )

# --- Input Schema ---
class TeamCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None

# --- Manual Serializer ---
def team_to_dict(team):
    children_list = team.children or []
    return {
        "id": team.id,
        "name": team.name,
        "parent_id": team.parent_id,
        "children": [team_to_dict(child) for child in children_list]
    }

# --- Routes ---

@router.post("/teams/")
def create_team(team: TeamCreate, db: Session = Depends(get_db)):
    try:
        if team.parent_id is not None:
            if team.parent_id <= 0:
                 raise HTTPException(status_code=400, detail="Invalid Parent ID")
            parent = db.query(Team).filter(Team.id == team.parent_id).first()
            if not parent:
                raise HTTPException(status_code=404, detail=f"Parent team {team.parent_id} not found")

        new_team = Team(name=team.name, parent_id=team.parent_id)
        db.add(new_team)
        db.commit()
        db.refresh(new_team)
        
        return JSONResponse(content={"id": new_team.id, "name": new_team.name, "status": "Created"})

    except Exception as e:
        print("!!! CREATE ERROR !!!", file=sys.stderr)
        traceback.print_exc()
        db.rollback()
        raise e

@router.get("/hierarchy/")
def get_hierarchy(db: Session = Depends(get_db)):
    try:
        # Fetch Roots
        roots = db.query(Team).filter(Team.parent_id == None).all()
        
        # Convert
        data = [team_to_dict(root) for root in roots]
        
        return JSONResponse(content=data)

    except Exception as e:
        print("!!! HIERARCHY ERROR !!!", file=sys.stderr)
        traceback.print_exc()
        return JSONResponse(content={"error": str(e)}, status_code=500)