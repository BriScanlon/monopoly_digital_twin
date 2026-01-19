import json
import os
from typing import List, Dict, Optional

class Board:
    def __init__(self, property_file_path: str = "data/london_properties.json"):
        self.spaces = [None] * 40  # 0 to 39
        self._load_properties(property_file_path)
        self._initialize_special_spaces()

    def _load_properties(self, file_path: str):
        """Loads property data from JSON and places them on the board."""
        # Resolve absolute path relative to the project root
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_path, file_path)

        with open(full_path, 'r', encoding='utf-8') as f:
            properties = json.load(f)

        for prop in properties:
            idx = prop['index']
            # Add dynamic fields for gameplay state
            prop['owner'] = None
            prop['houses'] = 0  # 5 houses = 1 hotel
            prop['mortgaged'] = False
            prop['type'] = 'property'
            self.spaces[idx] = prop

    def _initialize_special_spaces(self):
        """Fills in the non-property spaces (GO, Chance, Taxes, etc.)."""
        special_map = {
            0:  {"name": "GO", "type": "go"},
            2:  {"name": "Community Chest", "type": "community_chest"},
            4:  {"name": "Income Tax", "type": "tax", "amount": 200},
            7:  {"name": "Chance", "type": "chance"},
            10: {"name": "Jail", "type": "jail"}, # Just Visiting
            17: {"name": "Community Chest", "type": "community_chest"},
            20: {"name": "Free Parking", "type": "free_parking"},
            22: {"name": "Chance", "type": "chance"},
            30: {"name": "Go To Jail", "type": "go_to_jail"},
            33: {"name": "Community Chest", "type": "community_chest"},
            36: {"name": "Chance", "type": "chance"},
            38: {"name": "Luxury Tax", "type": "tax", "amount": 100}
        }

        for idx, info in special_map.items():
            self.spaces[idx] = info

    def get_space(self, index: int) -> Dict:
        """Returns the dictionary data for a specific board index."""
        if 0 <= index < 40:
            return self.spaces[index]
        raise IndexError(f"Board index {index} out of bounds (0-39).")

    def get_property_group(self, group_name: str) -> List[Dict]:
        """Returns all properties belonging to a specific color group (for Monopoly checks)."""
        return [s for s in self.spaces if s.get('type') == 'property' and s.get('group') == group_name]

    def reset(self):
        """Resets ownership and building state for a new game."""
        for space in self.spaces:
            if space.get('type') == 'property':
                space['owner'] = None
                space['houses'] = 0
                space['mortgaged'] = False