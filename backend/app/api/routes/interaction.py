from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.interaction import Interaction
from app.schemas.interaction import InteractionCreate, InteractionUpdate, InteractionResponse

router = APIRouter()

@router.post("/", response_model=InteractionResponse, status_code=status.HTTP_201_CREATED)
def create_interaction(interaction_in: InteractionCreate, db: Session = Depends(get_db)):
    db_interaction = Interaction(**interaction_in.model_dump())
    db.add(db_interaction)
    db.commit()
    db.refresh(db_interaction)
    return db_interaction

@router.get("/", response_model=List[InteractionResponse])
def read_interactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    interactions = db.query(Interaction).offset(skip).limit(limit).all()
    return interactions

@router.get("/{id}", response_model=InteractionResponse)
def read_interaction(id: int, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == id).first()
    if not interaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    return interaction

@router.put("/{id}", response_model=InteractionResponse)
def update_interaction(id: int, interaction_in: InteractionUpdate, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == id).first()
    if not interaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Interaction not found")
    
    update_data = interaction_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(interaction, key, value)
        
    db.commit()
    db.refresh(interaction)
    return interaction
