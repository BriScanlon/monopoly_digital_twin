import csv
import requests
import json
import random
from collections import defaultdict

# --- CONFIGURATION ---
CSV_FILE = "data/monopoly_smart_data.csv"
OLLAMA_URL = "http://localhost:11435/api/generate"
MODEL = "llama3"

def get_game_data(game_id=None):
    """
    Parses the CSV and retrieves rows for a specific game.
    If no game_id is provided, picks one with a Trade in it (more interesting).
    """
    games = defaultdict(list)
    interesting_games = []
    
    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            g_id = row['game_id']
            games[g_id].append(row)
            if row['decision'] == 'TRADE_ATTEMPT' and g_id not in interesting_games:
                interesting_games.append(g_id)
    
    if not game_id:
        # Pick a random game that had a trade attempt
        if not interesting_games:
            game_id = random.choice(list(games.keys()))
        else:
            game_id = random.choice(interesting_games)
            
    print(f"--- Analyzing Game ID: {game_id} ---")
    return games[game_id]

def summarize_game(rows):
    """
    Condenses 1000+ turns into a 'Highlight Reel' for the LLM.
    We can't send 500 lines of text, so we filter for key events.
    """
    highlights = []
    winner = None
    
    for row in rows:
        turn = row['turn_id']
        player = f"P{row['player_id']}"
        action = row['decision']
        result = row['result']
        cash = int(float(row['cash']))
        
        if row['victory_status'] == 'WINNER':
            winner = player
            
        # Filter for DRAMA
        if action == "TRADE_ATTEMPT":
            highlights.append(f"Turn {turn}: {player} attempts a strategic TRADE.")
        elif action == "BUY":
            highlights.append(f"Turn {turn}: {player} BUYS {row['space_name']} (Cash: {cash}).")
        elif action == "JAIL_EVENT" and "escape" in result:
             highlights.append(f"Turn {turn}: {player} escapes Jail!")
        elif "bankrupt" in result:
             highlights.append(f"Turn {turn}: {player} GOES BANKRUPT!")
        elif cash < 100 and int(turn) > 20:
             highlights.append(f"Turn {turn}: {player} is in financial trouble (Cash: {cash}).")
             
    return highlights, winner

def call_ollama(prompt):
    """Sends the prompt to the local Dockerized Llama 3."""
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json()['response']
    except Exception as e:
        return f"Error contacting Analyst Brain: {e}"

def run_analyst():
    # 1. Get Data
    game_rows = get_game_data()
    highlights, winner = summarize_game(game_rows)
    
    # 2. Construct Prompt
    # We give the LLM a persona
    prompt = f"""
    You are a high-energy Esports Commentator analyzing a match of 'LucenFlow Monopoly'.
    
    Here is the Match Log:
    {chr(10).join(highlights[-25:])}  <-- (Only showing last 25 key moments for brevity)
    
    The Winner was: {winner}
    
    Task:
    1. Write a short, exciting summary of the match.
    2. Analyze the Winner's strategy. Did they trade aggressively? Did they buy at the right time?
    3. Roast the losers slightly for their bad financial decisions.
    """
    
    print("... Asking Llama 3 for commentary (this may take a few seconds) ...\n")
    
    # 3. Generate
    commentary = call_ollama(prompt)
    
    print("="*60)
    print("🎙️  LUCENFLOW ANALYST REPORT")
    print("="*60)
    print(commentary)
    print("="*60)

if __name__ == "__main__":
    run_analyst()