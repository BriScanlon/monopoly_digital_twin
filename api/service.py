from fastapi import FastAPI, HTTPException
from ai.inference import MonopolyExpert
from api.schema import GameStateRequest, AnalysisResponse, DecisionResponse

app = FastAPI(title="LucenFlow Monopoly Expert API")

# Initialize the Expert
expert = MonopolyExpert(model_path="models/monopoly_ai_trading.pth")

@app.get("/")
def health_check():
    return {"status": "active", "version": "2.0", "model": "DQN-Trading"}

@app.post("/analyze/decision", response_model=AnalysisResponse)
def analyze_decision(request: GameStateRequest):
    """
    Unified Endpoint: Ask the AI what to do (Buy, Pass, or Trade).
    """
    result = expert.predict(request.state_vector)
    
    # Dynamic Narrative
    rec = result['recommendation']
    conf = result['confidence_score']
    q = result['q_values']
    
    if rec == "TRADE":
        narrative = (
            f"STRATEGIC ALERT: The Expert recommends initiating a TRADE (Confidence: {conf:.2f}). "
            f"It values the trading potential ({q['trade']:.1f}) higher than holding cash."
        )
    elif rec == "BUY":
        narrative = (
            f"The Expert recommends BUYING this property. "
            f"Projected value ({q['buy']:.1f}) exceeds the cost of passing ({q['pass']:.1f})."
        )
    else:
        narrative = (
            f"The Expert recommends PASSING. "
            f"Conserving cash is currently prioritized over this investment."
        )
    
    decision_data = DecisionResponse(
        recommendation=rec,
        confidence_score=conf,
        q_values=q
    )
    
    return AnalysisResponse(decision=decision_data, narrative=narrative)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)