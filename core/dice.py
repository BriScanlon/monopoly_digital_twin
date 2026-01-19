import random

class Dice:
    def __init__(self):
        self.die1 = 0
        self.die2 = 0
        self.doubles_count = 0  # Tracks consecutive doubles (3 = Jail)

    def roll(self):
        """
        Rolls two 6-sided dice.
        Returns:
            total (int): Sum of dice
            is_double (bool): True if die1 == die2
        """
        self.die1 = random.randint(1, 6)
        self.die2 = random.randint(1, 6)
        
        is_double = (self.die1 == self.die2)
        
        if is_double:
            self.doubles_count += 1
        else:
            self.doubles_count = 0
            
        return self.die1 + self.die2, is_double

    def reset_doubles(self):
        """Force reset doubles count (used when turn ends or player goes to jail)."""
        self.doubles_count = 0