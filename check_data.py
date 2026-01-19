import csv
from collections import Counter

FILE = "data/monopoly_smart_data.csv"

def analyze_data():
    print(f"--- Analyzing {FILE} ---")
    
    decisions = Counter()
    results = Counter()
    winners = Counter()
    
    try:
        with open(FILE, 'r') as f:
            reader = csv.DictReader(f)
            row_count = 0
            for row in reader:
                row_count += 1
                decisions[row['decision']] += 1
                results[row['result']] += 1
                if row['victory_status'] == 'WINNER':
                    winners[row['player_id']] += 1
                    
        print(f"Total Rows Scanned: {row_count}")
        print("\n--- Decision Breakdown ---")
        for action, count in decisions.items():
            pct = (count / row_count) * 100
            print(f"{action:<15}: {count:>6} ({pct:.1f}%)")
            
        print("\n--- Key Events ---")
        print(f"Trades Attempted: {decisions.get('TRADE_ATTEMPT', 0)}")
        print(f"Properties Bought: {decisions.get('BUY', 0)}")
        
        # Check balance
        print("\n--- Win Distribution (Should be roughly equal) ---")
        total_wins = sum(winners.values()) # This will be (rows where status=WINNER)
        # We actually want unique games won, but this proxy is fine for a quick check
        print(f"Player Wins (in rows): {dict(winners)}")

    except FileNotFoundError:
        print("❌ Error: File not found. Did you run the simulation?")

if __name__ == "__main__":
    analyze_data()