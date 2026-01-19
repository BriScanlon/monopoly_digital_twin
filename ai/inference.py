import torch
import numpy as np
import os
from ai.rl_agent import MonopolyNet
from core.board import Board

class MonopolyExpert:
    def __init__(self, model_path="models/monopoly_ai_trading.pth"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 1. Recreate the Model Architecture
        # Input: 205 features
        # Output: 3 actions (Pass, Buy, Trade)
        self.input_size = 205 
        self.model = MonopolyNet(self.input_size, 3).to(self.device)
        
        # 2. Load the Weights
        if os.path.exists(model_path):
            try:
                # Load weights (map_location ensures it loads even if moved from GPU to CPU)
                self.model.load_state_dict(torch.load(model_path, map_location=self.device))
                self.model.eval()
                print(f"Loaded Trading Expert from {model_path}")
            except Exception as e:
                print(f"ERROR loading model: {e}")
                print("Using random weights (Untrained)")
        else:
            print(f"WARNING: Model not found at {model_path}. Using random weights.")

    def predict(self, state_vector: list) -> dict:
        """
        Takes a raw list of 205 floats and returns the recommendation.
        """
        state_tensor = torch.FloatTensor(state_vector).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            q_values = self.model(state_tensor)
            
        # Extract values
        q_vals = q_values[0].tolist() # Convert tensor to list [v0, v1, v2]
        
        # Map indices to actions
        actions = ["PASS", "BUY", "TRADE"]
        best_action_idx = int(torch.argmax(q_values).item())
        recommendation = actions[best_action_idx]
        
        # Calculate Confidence (Gap between best and second best)
        sorted_q = sorted(q_vals, reverse=True)
        confidence = sorted_q[0] - sorted_q[1]
        
        return {
            "recommendation": recommendation,
            "confidence_score": confidence,
            "q_values": {
                "pass": q_vals[0],
                "buy": q_vals[1],
                "trade": q_vals[2]
            }
        }