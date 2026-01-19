from pydantic import BaseModel, Field
from typing import List, Dict

class GameStateRequest(BaseModel):
    state_vector: List[float] = Field(
        ..., 
        description="A list of 205 floating point numbers representing the encoded board state.",
        min_items=205,
        max_items=205
    )

class DecisionResponse(BaseModel):
    recommendation: str  # "BUY", "PASS", or "TRADE"
    confidence_score: float
    q_values: Dict[str, float] # {"pass": x, "buy": y, "trade": z}

class AnalysisResponse(BaseModel):
    decision: DecisionResponse
    narrative: str