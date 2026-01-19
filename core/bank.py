class Bank:
    def __init__(self, initial_cash: int = 20580, allow_infinite: bool = True):
        # Official Standard Monopoly Component Limits
        self.total_houses = 32
        self.total_hotels = 12
        
        # Financial Limits
        self.cash_reserves = initial_cash
        self.allow_infinite = allow_infinite  # If True, bank prints money (IOUs) when empty
        
        # Current Inventory
        self.houses_available = self.total_houses
        self.hotels_available = self.total_hotels

    # --- MONEY LOGIC ---
    def withdraw(self, amount: int) -> int:
        """
        Player or Engine requests money FROM the bank.
        Returns the actual amount given.
        """
        if self.cash_reserves >= amount:
            self.cash_reserves -= amount
            return amount
        else:
            if self.allow_infinite:
                # Bank prints money (IOU mode)
                self.cash_reserves -= amount # Goes negative to track deficit
                return amount
            else:
                # Hard Limit Mode: Bank gives whatever is left
                remaining = self.cash_reserves
                self.cash_reserves = 0
                return remaining

    def deposit(self, amount: int):
        """Player pays money TO the bank (Taxes, Buying properties)."""
        self.cash_reserves += amount

    # --- BUILDING LOGIC ---
    def can_build_house(self) -> bool:
        return self.houses_available > 0

    def can_build_hotel(self) -> bool:
        return self.hotels_available > 0

    def release_house(self):
        if self.houses_available > 0:
            self.houses_available -= 1
            return True
        return False

    def return_house(self):
        if self.houses_available < self.total_houses:
            self.houses_available += 1

    def release_hotel(self):
        if self.hotels_available > 0:
            self.hotels_available -= 1
            return True
        return False

    def return_hotel(self):
        if self.hotels_available < self.total_hotels:
            self.hotels_available += 1

    def reset(self):
        """Restocks the bank for a new game."""
        self.houses_available = self.total_houses
        self.hotels_available = self.total_hotels
        # Reset cash to standard London box amount
        self.cash_reserves = 20580