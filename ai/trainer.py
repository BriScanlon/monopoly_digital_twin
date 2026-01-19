import torch
import numpy as np
import os
import random
from core.engine import MonopolyEngine
from ai.rl_agent import Agent
from ai.state_encoder import StateEncoder

# --- TRY IMPORTING DIRECTML FOR AMD GPU ---
try:
    import torch_directml
    device = torch_directml.device()
    print(f"🚀 SUCCESS: AMD GPU Detected via DirectML ({device})")
except ImportError:
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"⚠️ DirectML not found. Using: {device}")

# --- CONFIGURATION ---
EPISODES = 2000
SAVE_INTERVAL = 100
MODEL_NAME = "monopoly_ai_trading.pth"

class TrainingEngine(MonopolyEngine):
    def __init__(self, agent, encoder):
        super().__init__(num_players=4)
        self.agent = agent
        self.encoder = encoder
        self.memories = [] 

    def _ai_decision_trade(self, player) -> bool:
        if player.id != self.current_player_idx: return False
        state = self.encoder.encode(player, self.players, self.board.spaces)
        action = self.agent.act(state)
        self.memories.append((state, action, player.id))
        return (action == 2)

    def _ai_decision_buy(self, player, space) -> bool:
        if player.id != self.current_player_idx:
            return (player.cash > space['price'])
        state = self.encoder.encode(player, self.players, self.board.spaces)
        action = self.agent.act(state)
        self.memories.append((state, action, player.id))
        return (action == 1)

def run_training():
    print(f"--- Starting GPU Training for {EPISODES} Episodes ---")
    
    encoder = StateEncoder()
    # Pass the GPU device to the Agent
    agent = Agent(state_size=encoder.observation_space_size, action_size=3)
    agent.device = device 
    agent.model.to(device) # Move Brain to GPU
    
    # SLOW DECAY: We want to reach min_epsilon (0.01) around episode 1500
    # Formula: 0.01 = 1.0 * (decay ^ 1500)  -> decay approx 0.997
    agent.epsilon_decay = 0.997 
    
    engine = TrainingEngine(agent, encoder)
    scores = []
    
    for e in range(1, EPISODES + 1):
        engine.reset(num_players=4)
        
        while not engine.game_over:
            current_player = engine.players[engine.current_player_idx]
            old_net_worth = current_player.get_net_worth(engine.board)
            engine.memories = []
            
            turn_result = engine.run_turn()
            
            # --- BATCH TRAINING ---
            if engine.memories:
                new_net_worth = current_player.get_net_worth(engine.board)
                base_reward = (new_net_worth - old_net_worth) / 100.0
                
                # Big reward for successful trades
                if turn_result.get('trade_event'):
                    base_reward += 10.0 
                
                # Penalty for bankruptcy
                if current_player.is_bankrupt:
                    base_reward = -10.0
                    done = True
                else:
                    done = False

                next_state = encoder.encode(current_player, engine.players, engine.board.spaces)
                
                # TRAIN LOOP
                for mem in engine.memories:
                    state, action, pid = mem
                    if pid == current_player.id:
                        agent.train(state, action, base_reward, next_state, done)

        # --- CORRECT DECAY LOCATION: ONCE PER GAME ---
        if agent.epsilon > agent.epsilon_min:
            agent.epsilon *= agent.epsilon_decay

        # Logging
        winner = max(engine.players, key=lambda p: p.get_net_worth(engine.board))
        scores.append(winner.get_net_worth(engine.board))
        
        if e % 50 == 0:
            avg = sum(scores[-50:]) / 50
            print(f"Ep {e}/{EPISODES} | Avg Win: £{avg:.0f} | Epsilon: {agent.epsilon:.4f}")
            
        if e % SAVE_INTERVAL == 0:
            os.makedirs("models", exist_ok=True)
            agent.save(f"models/{MODEL_NAME}")

    print("--- GPU Training Complete ---")

if __name__ == "__main__":
    run_training()