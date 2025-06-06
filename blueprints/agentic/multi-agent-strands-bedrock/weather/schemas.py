from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    """Request schema for query endpoints."""
    query: str
    session_id: Optional[str] = None