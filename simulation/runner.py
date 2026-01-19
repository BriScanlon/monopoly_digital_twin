import csv
import os
import torch
import random
from core.engine import MonopolyEngine
from ai.state_encoder import StateEncoder
from ai.rl_agent import MonopolyNet

# --- CONFIGURATION ---
NUM_GAMES = 500
MODEL_PATH = "models/monopoly_ai_trading.pth"
OUTPUT_FILE = "data/monopoly_smart_data.csv"

class SmartSimulationEngine(MonopolyEngine):
    def __init__(self, model, encoder, device):
        super().__init__(num_players=4)
        self.model = model
        self.encoder = encoder
        self.device = device

    def get_ai_action(self, player):
        state = self.encoder.encode(player, self.players, self.board.spaces)
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.model(state_tensor)
        return torch.argmax(q_values).item()

    def _ai_decision_trade(self, player) -> bool:
        action = self.get_ai_action(player)
        return (action == 2)

    def _ai_decision_buy(self, player, space) -> bool:
        action = self.get_ai_action(player)
        return (action == 1)

def run_simulation():
    print(f"--- Starting Smart Simulation ({NUM_GAMES} Games) ---")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using Device: {device}")
    
    model = MonopolyNet(input_size=205, output_size=3).to(device)
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
        model.eval()
        print(f"Loaded Model: {MODEL_PATH}")
    else:
        print("❌ ERROR: Model not found!")
        return

    encoder = StateEncoder()
    engine = SmartSimulationEngine(model, encoder, device)
    
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    with open(OUTPUT_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            "game_id", "turn_id", "player_id", "position", "space_name",
            "cash", "net_worth", "properties_owned", "in_jail", 
            "decision", "result", "victory_status"
        ])
        
        row_count = 0
        
        for g in range(1, NUM_GAMES + 1):
            engine.reset(num_players=4)
            game_history = []
            
            while not engine.game_over:
                current_player = engine.players[engine.current_player_idx]
                
                # Run turn
                log = engine.run_turn()
                
                # Skip turns that are just administrative (game over signals, etc)
                if log.get("event") == "game_over":
                    break

                # --- FIX: ROBUST DECISION LABELING ---
                decision_label = "PASS"
                result_str = log.get("result", "") # Default to empty if missing
                event_str = log.get("event", "")

                if log.get("trade_event"):
                    decision_label = "TRADE_ATTEMPT"
                elif "bought" in result_str:
                    decision_label = "BUY"
                elif "paid" in result_str:
                    decision_label = "PAY_RENT"
                elif "jail" in event_str:
                    decision_label = "JAIL_EVENT"
                    result_str = event_str # Use the event name as the result
                
                # --- SAFELY EXTRACT FIELDS ---
                # Some events (like Jail) might not have 'space' or 'cash' in the log
                # We fetch them from the player object directly to be safe
                pos = current_player.position
                space_name = engine.board.get_space(pos)['name']
                cash = current_player.cash
                
                game_history.append([
                    g, engine.turn_count, log.get('player', current_player.id), 
                    pos, space_name, cash, 
                    current_player.get_net_worth(engine.board),
                    len(current_player.properties), current_player.in_jail,
                    decision_label, result_str, "TBD"
                ])
                
            # Backfill Winner
            winner = max(engine.players, key=lambda p: p.get_net_worth(engine.board))
            for row in game_history:
                row[-1] = "WINNER" if row[2] == winner.id else "LOSER"
                writer.writerow(row)
                row_count += 1
            
            if g % 50 == 0:
                print(f"Simulated Game {g}/{NUM_GAMES} - Rows Generated: {row_count}")

    print(f"--- Simulation Complete. Data saved to {OUTPUT_FILE} ---")

if __name__ == "__main__":
    run_simulation()