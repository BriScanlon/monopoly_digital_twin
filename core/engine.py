import random
from typing import List, Dict, Any

from core.board import Board
from core.dice import Dice
from core.player import Player
from core.bank import Bank
from core.cards import CardManager

class MonopolyEngine:
    def __init__(self, num_players: int = 4):
        self.board = Board()
        self.dice = Dice()
        self.bank = Bank(initial_cash=20580, allow_infinite=True)
        self.card_manager = CardManager()
        self.players = [Player(i) for i in range(num_players)]
        
        self.current_player_idx = 0
        self.turn_count = 0
        self.game_over = False
        self.max_turns = 1000

    def reset(self, num_players: int = 4):
        self.board.reset()
        self.bank.reset()
        self.dice.reset_doubles()
        self.card_manager = CardManager()
        self.players = [Player(i) for i in range(num_players)]
        self.current_player_idx = 0
        self.turn_count = 0
        self.game_over = False

    def run_turn(self) -> Dict[str, Any]:
        if self.game_over:
            return {"event": "game_over"}

        player = self.players[self.current_player_idx]
        
        if player.is_bankrupt:
            self._next_player()
            return {"event": "skip", "player": player.id}

        if player.in_jail:
            return self._handle_jail_turn(player)

        # --- NEW: PRE-ROLL TRADING PHASE ---
        # The AI decides if it wants to try and trade BEFORE rolling
        trade_log = None
        if self._ai_decision_trade(player):
            trade_result = self._execute_trade_attempt(player)
            if trade_result:
                trade_log = trade_result

        # 1. Roll Dice
        roll_total, is_double = self.dice.roll()
        
        # Speeding Check
        if self.dice.doubles_count >= 3:
            player.go_to_jail()
            self._next_player()
            return {"event": "jail_speeding", "player": player.id}

        # 2. Move
        passed_go = player.move(roll_total)
        if passed_go:
            salary = self.bank.withdraw(200)
            player.receive(salary)

        # 3. Handle Landing
        current_space = self.board.get_space(player.position)
        result = self._handle_space_landing(player, current_space, roll_total)
        
        # 4. Post-Turn Logic
        if not is_double:
            self._next_player()
        elif player.is_bankrupt:
            self._next_player()
        
        self.turn_count += 1
        if self.turn_count >= self.max_turns:
            self.game_over = True

        # Return full log
        return {
            "player": player.id,
            "roll": roll_total,
            "is_double": is_double,
            "position": player.position,
            "space": current_space['name'],
            "cash": player.cash,
            "bank_cash": self.bank.cash_reserves,
            "result": result,
            "trade_event": trade_log # <--- Log the trade if it happened
        }

    def _handle_space_landing(self, player: Player, space: Dict, roll: int):
        space_type = space['type']

        if space_type == 'property':
            return self._handle_property(player, space)
        elif space_type == 'tax':
            amount = space['amount']
            if player.pay(amount):
                self.bank.deposit(amount)
                return f"paid_tax_{amount}"
            return "bankrupt"
        elif space_type == 'go_to_jail':
            player.go_to_jail()
            return "sent_to_jail"
        elif space_type == 'chance':
            card = self.card_manager.draw_chance()
            return self._apply_card(player, card, 'chance')
        elif space_type == 'community_chest':
            card = self.card_manager.draw_community_chest()
            return self._apply_card(player, card, 'community_chest')
        
        return "safe"

    def _handle_property(self, player: Player, space: Dict):
        owner_id = space['owner']
        
        if owner_id is None:
            # AI Hook for Buying
            if self._ai_decision_buy(player, space):
                if player.pay(space['price']):
                    self.bank.deposit(space['price'])
                    space['owner'] = player.id
                    player.properties.append(space['index'])
                    return "bought_property"
            return "passed_property"

        elif owner_id != player.id:
            if not space['mortgaged']:
                rent = self._calculate_rent(space, roll_val=0) 
                player.pay(rent)
                self.players[owner_id].receive(rent)
                return f"paid_rent_{rent}"
        
        return "owned_by_self"

    def _calculate_rent(self, space: Dict, roll_val: int) -> int:
        if space['group'] in ['Utility']:
            return 28 
        if space['group'] == 'Station':
            owner_props = [p for p in self.players[space['owner']].properties if self.board.get_space(p)['group'] == 'Station']
            count = len(owner_props)
            return [0, 25, 50, 100, 200][count] if count <= 4 else 200
            
        houses = space['houses']
        if houses == 0:
             return space['rent'][0] 
        return space['rent'][houses]

    # --- DECISION HOOKS (To be overridden by AI) ---
    def _ai_decision_buy(self, player: Player, space: Dict) -> bool:
        """Default Heuristic: Buy if affordable."""
        return player.cash > space['price'] + 50

    def _ai_decision_trade(self, player: Player) -> bool:
        """Default Heuristic: Never initiate trades."""
        return False

    # --- TRADING LOGIC ---
    def _execute_trade_attempt(self, player: Player):
        """
        Attempts to find a 'Set Completer' property owned by another player
        and buys it for cash.
        """
        # 1. Identify needed properties
        # Simple Logic: Look at groups where I own at least 1 property, but not all.
        owned_groups = {}
        for pid in player.properties:
            prop = self.board.get_space(pid)
            grp = prop['group']
            if grp not in owned_groups: owned_groups[grp] = []
            owned_groups[grp].append(pid)
            
        target_prop_index = None
        target_owner_id = None
        
        # Find the first missing piece of a set
        for grp, pids in owned_groups.items():
            # Get all props in this group from board
            all_in_group = [s for s in self.board.spaces if s.get('group') == grp]
            if len(pids) < len(all_in_group):
                # We are missing one! Find who has it.
                for space in all_in_group:
                    if space['index'] not in pids:
                        if space['owner'] is not None and space['owner'] != player.id:
                            target_prop_index = space['index']
                            target_owner_id = space['owner']
                            break
            if target_prop_index: break
            
        if not target_prop_index:
            return None # Nothing useful to trade for

        # 2. Formulate Offer (Face Value * 2)
        target_space = self.board.get_space(target_prop_index)
        offer_price = target_space['price'] * 2
        
        # Check affordability
        if player.cash < offer_price:
            return None

        # 3. Opponent Decision (Heuristic)
        # Opponent accepts if they have low cash (< 500) OR if the offer is huge (3x price - though we offered 2x)
        # For now, let's say Opponent accepts if they are NOT close to a monopoly themselves in that group
        opponent = self.players[target_owner_id]
        
        if opponent.cash < 500: # Need cash badly
            # EXECUTE TRADE
            player.pay(offer_price)
            opponent.receive(offer_price)
            
            # Transfer Deed
            target_space['owner'] = player.id
            opponent.properties.remove(target_prop_index)
            player.properties.append(target_prop_index)
            
            return f"trade_success_bought_{target_space['name']}"
            
        return "trade_rejected"

    def _apply_card(self, player: Player, card: Dict, deck_type: str):
        if not card: return "no_card"
        action = card['action']
        val = card['value']
        if action == 'move_abs':
            player.position = val
            return f"moved_to_{val}"
        elif action == 'earn':
            amount = self.bank.withdraw(val)
            player.receive(amount)
        elif action == 'pay':
            if player.pay(val):
                self.bank.deposit(val)
        elif action == 'go_jail':
            player.go_to_jail()
        return f"card_{action}"

    def _handle_jail_turn(self, player: Player):
        roll, is_double = self.dice.roll()
        if is_double:
            player.in_jail = False
            player.move(roll)
            return {"event": "jail_escape_doubles"}
        player.turns_in_jail += 1
        if player.turns_in_jail >= 3:
            if player.pay(50):
                self.bank.deposit(50)
                player.in_jail = False
                player.move(roll)
                return {"event": "jail_forced_exit"}
        self._next_player()
        return {"event": "jail_stay"}

    def _next_player(self):
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)