from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class InteractionBase(BaseModel):
    hcp_name: str
    specialty: Optional[str] = None
    product: str
    interaction_date: datetime
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    next_action: Optional[str] = None

class InteractionCreate(InteractionBase):
    pass

class InteractionUpdate(BaseModel):
    hcp_name: Optional[str] = None
    specialty: Optional[str] = None
    product: Optional[str] = None
    interaction_date: Optional[datetime] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    next_action: Optional[str] = None

class InteractionResponse(InteractionBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
