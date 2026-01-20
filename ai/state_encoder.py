import numpy as np
import torch

class StateEncoder:
    def __init__(self):
        # 40 spaces on the board.
        # This heatmap represents the statistical probability of landing on a square.
        # Source: Standard Monopoly Monte Carlo simulations.
        # High peaks: Jail exits (Oranges/Reds) and Railroads.
        # Low valleys: Brown, Dark Blue, and the "Green Graveyard".
        self.heatmap = [
            2.1,  # 00 GO
            1.7,  # 01 Old Kent Road (Brown)
            1.8,  # 02 Community Chest
            1.7,  # 03 Whitechapel Road (Brown)
            2.0,  # 04 Income Tax
            2.9,  # 05 Kings Cross Station (Rail)
            2.3,  # 06 The Angel Islington (L.Blue)
            1.0,  # 07 Chance
            2.3,  # 08 Euston Road (L.Blue)
            2.4,  # 09 Pentonville Road (L.Blue)
            5.9,  # 10 JAIL (Just visiting + In Jail)
            2.7,  # 11 Pall Mall (Pink)
            2.6,  # 12 Electric Company
            2.3,  # 13 Whitehall (Pink)
            2.4,  # 14 Northumberland Avenue (Pink)
            2.8,  # 15 Marylebone Station (Rail)
            2.8,  # 16 Bow Street (Orange) - HIGH VALUE
            1.0,  # 17 Community Chest
            2.9,  # 18 Marlborough Street (Orange) - HIGH VALUE
            3.0,  # 19 Vine Street (Orange) - PEAK VALUE
            2.2,  # 20 Free Parking
            2.6,  # 21 Strand (Red)
            1.1,  # 22 Chance
            2.6,  # 23 Fleet Street (Red)
            2.7,  # 24 Trafalgar Square (Red)
            2.9,  # 25 Fenchurch St Station (Rail)
            2.6,  # 26 Leicester Square (Yellow)
            2.6,  # 27 Coventry Street (Yellow)
            2.7,  # 28 Water Works
            2.6,  # 29 Piccadilly (Yellow)
            2.4,  # 30 GO TO JAIL (Target, not landable really)
            2.5,  # 31 Regent Street (Green)
            2.5,  # 32 Oxford Street (Green)
            1.0,  # 33 Community Chest
            2.4,  # 34 Bond Street (Green)
            2.8,  # 35 Liverpool St Station (Rail)
            0.9,  # 36 Chance
            2.1,  # 37 Park Lane (D.Blue) - SURPRISINGLY LOW
            2.1,  # 38 Super Tax
            2.6   # 39 Mayfair (D.Blue)
        ]

    def encode(self, player, all_players, board_spaces):
        """
        Converts the game state into a flat vector for the Neural Network.
        Size: ~205 floats
        """
        state = []

        # --- 1. GLOBAL GAME STATE (Turn count approx, etc) ---
        # Normalized turn count (0.0 to 1.0, assuming max 100 turns roughly)
        # We don't have turn count passed here easily, so skipping or relying on cash/props as proxy.
        
        # --- 2. CURRENT PLAYER STATUS (4 inputs) ---
        state.append(player.position / 40.0)  # Norm Position
        state.append(player.cash / 5000.0)    # Norm Cash (Scale down)
        state.append(1.0 if player.in_jail else 0.0)
        state.append(player.get_net_worth_raw() / 10000.0) # Approx Net Worth

        # --- 3. OTHER PLAYERS STATUS (3 opponents * 4 inputs = 12) ---
        for p in all_players:
            if p.id != player.id:
                state.append(p.position / 40.0)
                state.append(p.cash / 5000.0)
                state.append(1.0 if p.in_jail else 0.0)
                state.append(p.get_net_worth_raw() / 10000.0)

        # --- 4. BOARD PROPERTY STATE (40 spaces * X features) ---
        # For every space, we tell the AI:
        # - Who owns it? (0=None, 1=Me, -1=Opponent)
        # - Is it mortgaged?
        # - Is it a full set? (Monopoly active)
        # - VALUE HEATMAP (New!)
        
        for i, space in enumerate(board_spaces):
            # Feature 1: Ownership
            owner_val = 0
            if space['owner'] is not None:
                owner_val = 1 if space['owner'] == player.id else -1
            state.append(owner_val)

            # Feature 2: Heatmap Value (The Strategic Upgrade)
            # We inject the probability of landing here.
            # This teaches the AI that Orange > Green.
            state.append(self.heatmap[i] / 6.0) # Normalize roughly

            # Feature 3: Mortgaged?
            state.append(1.0 if space.get('mortgaged') else 0.0)
            
            # Feature 4: House Count (0-5, normalized)
            # 5 = Hotel
            houses = space.get('houses', 0)
            state.append(houses / 5.0)

        return np.array(state, dtype=np.float32)