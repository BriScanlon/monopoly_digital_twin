import json
import random
import os
from collections import deque

class CardDeck:
    def __init__(self, deck_file: str):
        self.cards = deque()
        self._load_deck(deck_file)
        self.shuffle()

    def _load_deck(self, file_path: str):
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        full_path = os.path.join(base_path, file_path)
        
        with open(full_path, 'r', encoding='utf-8') as f:
            card_list = json.load(f)
            for card in card_list:
                self.cards.append(card)

    def shuffle(self):
        """Randomizes the order of the deck."""
        temp_list = list(self.cards)
        random.shuffle(temp_list)
        self.cards = deque(temp_list)

    def draw(self):
        """Draws the top card. If it's not 'Get Out of Jail Free', it goes to the bottom."""
        if not self.cards:
            return None
        
        card = self.cards.popleft()
        
        # If it is NOT a "Get Out of Jail Free" card, put it back at the bottom immediately.
        # If it IS a GOOJF card, the player keeps it, so we don't return it to the deck yet.
        if card['action'] != 'jail_free':
            self.cards.append(card)
            
        return card

    def return_jail_card(self, card):
        """Used when a player plays or sells a Get Out of Jail Free card."""
        self.cards.append(card)

class CardManager:
    def __init__(self):
        self.chance = CardDeck("data/chance_deck.json")
        self.community_chest = CardDeck("data/comm_chest.json")

    def draw_chance(self):
        return self.chance.draw()

    def draw_community_chest(self):
        return self.community_chest.draw()
    
    def return_jail_card(self, card, deck_type):
        if deck_type == 'chance':
            self.chance.return_jail_card(card)
        else:
            self.community_chest.return_jail_card(card)