class Player:
    def __init__(self, player_id: int, initial_cash: int = 1500):
        self.id = player_id
        self.cash = initial_cash
        self.position = 0  # Index 0-39 (Starts at GO)
        self.properties = []  # List of property indices owned
        self.in_jail = False
        self.turns_in_jail = 0
        self.get_out_of_jail_cards = 0
        self.is_bankrupt = False

    def move(self, steps: int):
        """Updates position. Returns True if passed GO."""
        new_position = (self.position + steps) % 40
        passed_go = new_position < self.position and steps > 0
        self.position = new_position
        return passed_go

    def pay(self, amount: int):
        """Deducts cash. Returns False if insufficient funds (needs bankruptcy logic)."""
        if self.cash >= amount:
            self.cash -= amount
            return True
        else:
            # In the full engine, this triggers the "raise funds" logic
            self.cash -= amount # Allow negative temporarily to signal debt
            return False

    def receive(self, amount: int):
        """Adds cash to player wallet."""
        self.cash += amount

    def go_to_jail(self):
        """Teleports player to Jail (Index 10) and sets status."""
        self.position = 10
        self.in_jail = True
        self.turns_in_jail = 0

    def get_net_worth(self, board) -> int:
        """Calculates total value (Cash + Property Value + Buildings)."""
        asset_value = 0
        for prop_idx in self.properties:
            prop = board.get_space(prop_idx)
            # Add face value
            asset_value += prop['price']
            # Add building values (Houses/Hotels cost money to build)
            if prop['houses'] > 0:
                # Note: This is simplified. Accurate calculation requires knowing house cost per property.
                # In simulation, we usually look up the house_cost from the board data.
                asset_value += (prop['houses'] * prop.get('house_cost', 0))
        
        return self.cash + asset_value