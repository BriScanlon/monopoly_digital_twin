import numpy as np
from core.board import Board
from core.player import Player

class StateEncoder:
    def __init__(self):
        self.board_size = 40
        # We need to know the board layout to encode properties correctly
        self.board_ref = Board()
        
    def encode(self, player: Player, all_players: list, board_state: list) -> np.ndarray:
        """
        Converts the game state into a numerical vector for the AI.
        """
        # 1. Player Data (Cash normalized, Position) - [2 floats]
        # We normalize cash by dividing by 2000 (roughly starting cash + buffer)
        player_data = [
            min(player.cash / 3000.0, 1.0), 
            player.position / 40.0
        ]
        
        # 2. Property State - [40 * 3 floats]
        # For each square, we track: Is it mine? Is it theirs? Is it mortgaged?
        # Note: We treat all opponents as a single "Enemy" entity for the input vector 
        # to keep the input size fixed, or we track specific ownership.
        # Here we use: [Is_Mine, Is_Opponent, Is_Unowned, Has_Houses_Norm]
        
        prop_data = []
        for idx in range(40):
            space = board_state[idx]
            space_type = space.get('type')
            
            if space_type == 'property':
                owner = space.get('owner')
                houses = space.get('houses', 0)
                is_mortgaged = 1.0 if space.get('mortgaged') else 0.0
                
                is_mine = 1.0 if owner == player.id else 0.0
                is_opponent = 1.0 if (owner is not None and owner != player.id) else 0.0
                is_unowned = 1.0 if owner is None else 0.0
                
                # Normalize houses (0 to 5)
                house_level = houses / 5.0
                
                prop_data.extend([is_mine, is_opponent, is_unowned, house_level, is_mortgaged])
            else:
                # Padding for non-property spaces to keep vector aligned
                prop_data.extend([0.0, 0.0, 0.0, 0.0, 0.0])

        # 3. Game Context - [3 floats]
        # Jail status, etc.
        context_data = [
            1.0 if player.in_jail else 0.0,
            len(all_players) / 6.0, # Normalized player count
            1.0 if any(p.is_bankrupt for p in all_players) else 0.0
        ]
        
        # Combine all parts
        full_vector = player_data + prop_data + context_data
        return np.array(full_vector, dtype=np.float32)

    @property
    def observation_space_size(self):
        # Calculate the total length of the vector
        # 2 (Player) + 40*5 (Props) + 3 (Context) = 205 inputs
        return 2 + (40 * 5) + 3