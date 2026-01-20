class Player:
    def __init__(self, player_id, name, start_cash=1500):
        self.id = player_id
        self.name = name
        self.cash = start_cash
        self.position = 0
        self.properties = []  # List of property objects/dicts
        self.in_jail = False
        self.jail_turns = 0
        self.get_out_of_jail_card = False

    def pay(self, amount):
        """Standard payment logic. Returns amount paid (or max available)."""
        if self.cash >= amount:
            self.cash -= amount
            return amount
        else:
            # Bankrupt/Debt logic would go here. 
            # For now, we drain them to 0.
            paid = self.cash
            self.cash = 0
            return paid

    def receive(self, amount):
        """Add cash."""
        self.cash += amount

    def move(self, steps, board_size=40):
        """Moves the player and handles wrapping around GO."""
        new_position = (self.position + steps) % board_size
        # Check for passing GO (simple logic)
        if new_position < self.position and steps > 0:
            self.receive(200) # Pass GO Bonus
        self.position = new_position

    def buy_property(self, property_data):
        """Adds a property to the portfolio."""
        # Ensure we store the cost/value for net worth calc
        self.cash -= property_data['price']
        self.properties.append(property_data)

    def get_net_worth(self, board):
        """
        Precise Net Worth: Cash + Property Value + House Values.
        Requires board access to check house counts.
        """
        asset_value = 0
        for prop in self.properties:
            asset_value += prop['price']
            # If we had houses logic, we would query the board here:
            # houses = board.spaces[prop['id']].get('houses', 0)
            # asset_value += houses * prop['house_cost']
        return self.cash + asset_value

    def get_net_worth_raw(self):
        """
        Fast Net Worth for the AI Encoder.
        Does not require board access (ignores House values for speed).
        """
        asset_value = sum(p['price'] for p in self.properties)
        return self.cash + asset_value

    def __repr__(self):
        return f"Player({self.id}, Cash: {self.cash}, Props: {len(self.properties)})"