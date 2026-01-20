import torch
import numpy as np
import os
import random
from core.engine import MonopolyEngine
from ai.state_encoder import StateEncoder
from ai.rl_agent import Agent

# --- HYPERPARAMETERS ---
EPISODES = 2000
BATCH_SIZE = 64
GAMMA = 0.99
EPSILON_START = 1.0
EPSILON_END = 0.01
EPSILON_DECAY = 0.998 
TARGET_UPDATE = 10
MAX_STEPS_PER_GAME = 200  # Prevents infinite stalemates

# --- SMART ENGINE SUBCLASS ---
class TrainingEngine(MonopolyEngine):
    def __init__(self):
        super().__init__()
        self.ai_decision = 0 # 0=Pass, 1=Buy, 2=Trade

    def set_ai_decision(self, action):
        self.ai_decision = action

    def _handle_property(self, player, space, log):
        """Overrides the core engine's property handling."""
        if space['owner'] is None:
            # AI DECISION POINT
            can_afford = player.cash > space['price']
            
            # If Action 1 (Buy) is chosen, we buy.
            # If Action 2 (Trade) is chosen, we also buy (don't miss assets while trading).
            wants_to_buy = (self.ai_decision == 1) or (self.ai_decision == 2)

            if can_afford and wants_to_buy:
                player.buy_property(space)
                space['owner'] = player.id
                log['result'] = "bought_property"
            else:
                log['result'] = "pass_choice" if can_afford else "pass_no_money"
                
        elif space['owner'] != player.id:
            rent = space['rent']
            amount = player.pay(rent)
            self.players[space['owner']].receive(amount)
            log['result'] = f"paid_rent_{amount}"
        else:
            log['result'] = "already_owned"

def calculate_reward(player, prev_state, log, trade_success):
    reward = 0
    action_result = log.get('result', '')
    
    # 1. THE PANIC BUTTON (Liquidity check)
    if player.cash < 50:
        reward -= 20.0 # Extreme Danger
    elif player.cash < 200:
        reward -= 5.0  # Caution
        
    # 2. TRADE REWARD
    if trade_success:
        print(f"\n💰 AI MADE A DEAL! ({log['player']})")
        reward += 30.0 
        
    # 3. BUYING LOGIC
    if "bought_property" in action_result:
        if player.cash > 250:
            reward += 10.0
        else:
            reward -= 5.0 # Risky buy
            
    # 4. BANKRUPTCY
    if "bankrupt" in action_result:
        return -500.0

    # 5. SURVIVAL
    reward += 0.1
    
    return reward

def train():
    print("--- Initializing Strategy Training (Set Completer) ---")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    engine = TrainingEngine()
    encoder = StateEncoder()
    # Corrected input size for the new Encoder
    agent = Agent(state_size=176, action_size=3, device=device)
    
    # Load previous brain
    if os.path.exists("models/monopoly_ai_trading.pth"):
        try:
            agent.model.load_state_dict(torch.load("models/monopoly_ai_trading.pth"))
            agent.epsilon = 0.4 
            print("Loaded existing brain.")
        except:
            print("Starting fresh.")

    for e in range(1, EPISODES + 1):
        engine.reset()
        state = encoder.encode(engine.players[0], engine.players, engine.board.spaces)
        
        total_reward = 0
        done = False
        step_count = 0
        
        while not done and step_count < MAX_STEPS_PER_GAME:
            step_count += 1
            current_player = engine.players[engine.current_player_idx]
            
            # 1. AI Action
            action = agent.act(state)
            
            # 2. Configure Engine
            engine.set_ai_decision(action)
            
            # 3. Execute Turn
            log = engine.run_turn()
            
            # 4. Handle TRADING
            trade_happened = False
            if action == 2 and not engine.game_over:
                success, msg = engine.try_smart_trade(current_player.id)
                if success:
                    trade_happened = True
                    log['result'] = msg 
            
            # 5. Reward & Train
            next_state = encoder.encode(current_player, engine.players, engine.board.spaces)
            reward = calculate_reward(current_player, state, log, trade_happened)
            
            if current_player.id == 0:
                agent.train(state, action, reward, next_state, engine.game_over)
                total_reward += reward
                state = next_state
            
            if step_count >= MAX_STEPS_PER_GAME:
                done = True
            else:
                done = engine.game_over

        # Epsilon Decay
        if agent.epsilon > EPSILON_END:
            agent.epsilon *= EPSILON_DECAY
        
        # Feedback
        if e % 10 == 0:
            print(f"Ep {e}...", end="\r")
            
        if e % 100 == 0:
            print(f"Ep {e}/{EPISODES} | Reward: {total_reward:.1f} | Epsilon: {agent.epsilon:.2f}")
            agent.save("models/monopoly_ai_trading.pth")

    print("\n--- Strategy Training Complete ---")

if __name__ == "__main__":
    train()