import random
import json
from .player import Player

class Board:
    def __init__(self):
        self.spaces = self._init_spaces()
        # Define color groups for "Set Completer" logic
        self.color_groups = {
            "Brown": [1, 3],
            "L.Blue": [6, 8, 9],
            "Pink": [11, 13, 14],
            "Orange": [16, 18, 19],
            "Red": [21, 23, 24],
            "Yellow": [26, 27, 29],
            "Green": [31, 32, 34],
            "D.Blue": [37, 39]
        }

    def _init_spaces(self):
        spaces = []
        groups = ["Brown", "L.Blue", "Pink", "Orange", "Red", "Yellow", "Green", "D.Blue"]
        group_prices = [60, 100, 140, 180, 220, 260, 300, 350] 
        
        for i in range(40):
            space = {
                "id": i,
                "name": f"Space {i}",
                "type": "property",
                "price": 0,
                "rent": 0,
                "owner": None,
                "houses": 0,
                "mortgaged": False,
                "group": None
            }
            
            if i % 10 == 0:
                space["type"] = "corner"
                space["name"] = ["GO", "Jail", "Free Parking", "Go To Jail"][i//10]
            elif i in [2, 7, 17, 22, 33, 36]:
                space["type"] = "action"
                space["name"] = "Community Chest" if i in [2, 17, 33] else "Chance"
            elif i in [4, 38]:
                space["type"] = "tax"
                space["name"] = "Income Tax" if i == 4 else "Super Tax"
                space["rent"] = 200 if i == 4 else 100
            elif i in [5, 15, 25, 35]:
                space["type"] = "railroad"
                space["name"] = f"Station {i}"
                space["price"] = 200
                space["rent"] = 25
                space["group"] = "Rail"
            elif i in [12, 28]:
                space["type"] = "utility"
                space["name"] = "Utility"
                space["price"] = 150
                space["group"] = "Utility"
            else:
                g_idx = 0
                if i > 5: g_idx = 1
                if i > 10: g_idx = 2
                if i > 15: g_idx = 3 
                if i > 20: g_idx = 4
                if i > 25: g_idx = 5
                if i > 30: g_idx = 6
                if i > 35: g_idx = 7
                
                space["group"] = groups[g_idx]
                space["price"] = group_prices[g_idx]
                space["rent"] = int(space["price"] * 0.1)
                space["name"] = f"{space['group']} Street {i}"
                
                if i == 39: space["name"] = "Mayfair"
                if i == 37: space["name"] = "Park Lane"
                if i == 19: space["name"] = "Vine Street" 

            spaces.append(space)
        return spaces

    def get_space(self, index):
        return self.spaces[index]

class MonopolyEngine:
    def __init__(self, num_players=4):
        self.board = Board()
        self.players = [Player(i, f"Player {i}") for i in range(num_players)]
        self.current_player_idx = 0
        self.turn_count = 0
        self.game_over = False

    def reset(self, num_players=4):
        self.board = Board()
        self.players = [Player(i, f"Player {i}") for i in range(num_players)]
        self.current_player_idx = 0
        self.turn_count = 0
        self.game_over = False

    def roll_dice(self):
        d1 = random.randint(1, 6)
        d2 = random.randint(1, 6)
        return d1 + d2, (d1 == d2)

    def run_turn(self):
        if self.game_over:
            return {"event": "game_over"}

        player = self.players[self.current_player_idx]
        
        if player.cash <= 0:
            self._next_turn()
            return {"player": player.id, "event": "skip_bankrupt", "result": "bankrupt"}

        # 1. Roll & Move
        steps, double = self.roll_dice()
        
        if player.in_jail:
            if double:
                player.in_jail = False
                player.jail_turns = 0
            else:
                player.jail_turns += 1
                if player.jail_turns >= 3:
                    player.pay(50)
                    player.in_jail = False
                    player.jail_turns = 0
                else:
                    self._next_turn()
                    return {"player": player.id, "space": "Jail", "result": "jail_stay", "cash": player.cash}

        player.move(steps)
        space = self.board.get_space(player.position)
        
        log = {
            "player": player.id,
            "position": player.position,
            "space": space['name'],
            "cash": player.cash,
            "trade_event": False
        }

        # 2. Handle Space Event
        if space['type'] == 'property' or space['type'] == 'railroad' or space['type'] == 'utility':
            self._handle_property(player, space, log)
        elif space['type'] == 'tax':
            player.pay(space['rent'])
            log['result'] = f"paid_tax_{space['rent']}"
        elif space['name'] == "Go To Jail":
            player.position = 10 
            player.in_jail = True
            log['result'] = "sent_to_jail"
        else:
            log['result'] = "landed_safe"

        self._next_turn()
        return log

    def _handle_property(self, player, space, log):
        if space['owner'] is None:
            if player.cash > space['price']:
                player.buy_property(space)
                space['owner'] = player.id
                log['result'] = "bought_property"
            else:
                log['result'] = "pass_no_money"
        elif space['owner'] != player.id:
            rent = space['rent']
            amount = player.pay(rent)
            owner = self.players[space['owner']]
            owner.receive(amount)
            log['result'] = f"paid_rent_{amount}"
        else:
            log['result'] = "already_owned"

    def try_smart_trade(self, player_idx):
        """
        PRIORITY 3 & 4: Set Completer with Defensive Awareness.
        """
        player = self.players[player_idx]
        
        # 1. Identify "Missing Links"
        target_group = None
        missing_id = None
        
        for group, ids in self.board.color_groups.items():
            owned_count = sum(1 for i in ids if self.board.spaces[i]['owner'] == player.id)
            if owned_count == len(ids) - 1:
                # We are 1 away!
                for i in ids:
                    if self.board.spaces[i]['owner'] != player.id and self.board.spaces[i]['owner'] is not None:
                        target_group = group
                        missing_id = i
                        break
            if target_group: break
        
        if not target_group:
            return False, "no_strategic_targets"

        # 2. Formulate Offer
        target_space = self.board.spaces[missing_id]
        target_owner_id = target_space['owner']
        target_owner = self.players[target_owner_id]
        
        # Base Offer: 2.5x Market Value (Increased from 2.0x because bots are smarter now)
        offer_price = int(target_space['price'] * 2.5)
        
        # 3. Defensive Check (Self-Awareness)
        # If we know this trade completes our set, we know the opponent *should* charge us more.
        # We increase our offer to 4x to tempt them, IF we have the cash.
        if player.cash > (offer_price * 2):
            offer_price = int(target_space['price'] * 4.0)
        
        # Do we have the cash?
        if player.cash < offer_price + 20: 
            return False, "too_poor_to_trade"
            
        # 4. Propose to Opponent
        # We now pass 'player' (the buyer) so the seller knows who they are dealing with
        if self._accept_trade(target_owner, offer_price, target_space, player):
            # Execute
            player.pay(offer_price)
            target_owner.receive(offer_price)
            
            target_space['owner'] = player.id
            player.properties.append(target_space)
            target_owner.properties = [p for p in target_owner.properties if p['id'] != missing_id]
            
            return True, f"traded_for_{target_space['name']}"
            
        return False, "offer_rejected"

    def _accept_trade(self, seller, cash_offer, property_at_stake, buyer):
        """
        PRIORITY 4: Defensive Blocking.
        The seller decides based on value AND threat level.
        """
        valuation = property_at_stake['price']
        
        # 1. DETECT THREAT (Kingmaker Scenario)
        # Does this trade give the BUYER a monopoly?
        group = property_at_stake['group']
        group_ids = self.board.color_groups.get(group, [])
        
        # Count what the buyer ALREADY has
        buyer_owns = sum(1 for i in group_ids if self.board.spaces[i]['owner'] == buyer.id)
        
        # If they have (Total - 1), this card is the final piece.
        completes_monopoly = (buyer_owns == len(group_ids) - 1)

        # 2. DECISION LOGIC
        if completes_monopoly:
            
            # This is a dangerous trade.
            # If the seller is wealthy, they should flat out REFUSE to help the enemy.
            if seller.cash > 300:
                return False 
            
            # If seller is poor/average, they demand a 'Kingmaker Premium' (5x value)
            return cash_offer > (valuation * 5.0)

        # 3. Standard Trade (Non-threatening)
        # If I am broke, I sell cheap
        if seller.cash < 100:
            return cash_offer > valuation
            
        # Normal greed
        return cash_offer > (valuation * 2.5)

    def _next_turn(self):
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)
        self.turn_count += 1