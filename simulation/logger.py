import csv
import os
from typing import List, Dict, Any

class SimulationLogger:
    def __init__(self, filename: str = "sim_data_001.csv", buffer_size: int = 10000):
        # Define output path
        self.output_dir = os.path.join("data", "raw_simulations")
        os.makedirs(self.output_dir, exist_ok=True)
        self.filepath = os.path.join(self.output_dir, filename)
        
        self.buffer: List[Dict] = []
        self.buffer_size = buffer_size
        
        # specific columns we want to track for ML training
        self.fieldnames = [
            "game_id", "turn_number", "player_id", "total_players", # <--- Added total_players
            "position", "cash", "bank_cash", # <--- Added bank_cash
            "net_worth", "properties_owned", 
            "in_jail", "action_taken", 
            "result_outcome", "game_winner" 
        ]

    def log_turn(self, game_id: int, turn_num: int, total_players: int, player_obj, action: str, result: str, bank_cash: int):
        """
        Staging area: Validates data and adds to temporary memory.
        """
        row = {
            "game_id": game_id,
            "turn_number": turn_num,
            "player_id": player_obj.id,
            "total_players": total_players, # <--- Capture the new argument
            "position": player_obj.position,
            "cash": player_obj.cash,
            "bank_cash": bank_cash,         # <--- Capture the new argument
            "net_worth": player_obj.cash,   # Placeholder for full net worth calc
            "properties_owned": len(player_obj.properties), 
            "in_jail": 1 if player_obj.in_jail else 0,
            "action_taken": action,
            "result_outcome": result,
            "game_winner": None # Placeholder until game ends
        }
        self.buffer.append(row)
        
        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self):
        """Writes the buffer to disk."""
        if not self.buffer:
            return

        file_exists = os.path.isfile(self.filepath)
        
        with open(self.filepath, mode='a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.fieldnames)
            
            if not file_exists:
                writer.writeheader()
                
            writer.writerows(self.buffer)
        
        self.buffer.clear()

    def finalize(self):
        """Force write remaining data at end of simulation."""
        self.flush()