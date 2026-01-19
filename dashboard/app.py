import sys
import os

import streamlit as st
import pandas as pd
import time
import torch
import random
from core.engine import MonopolyEngine
from ai.inference import MonopolyExpert
from analyst.agent import call_ollama



# --- PATH FIX ---
# This tells Python to look for modules in the project root (one level up)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="LucenFlow AI: Monopoly Expert",
    page_icon="🎩",
    layout="wide"
)

# --- CACHED RESOURCES (Load once) ---
@st.cache_resource
def load_expert():
    # Load the GPU Brain
    return MonopolyExpert(model_path="models/monopoly_ai_trading.pth")

@st.cache_resource
def load_engine():
    # Initialize a fresh engine
    return MonopolyEngine(num_players=4)

expert = load_expert()
# We don't cache the engine state itself, just the class/structure if needed
# But for Streamlit session state, we manage the engine instance manually below.

# --- SESSION STATE INITIALIZATION ---
if 'engine' not in st.session_state:
    st.session_state.engine = MonopolyEngine(num_players=4)
    st.session_state.game_log = []
    st.session_state.turn_count = 0
    st.session_state.analyst_commentary = "Waiting for game data..."

# --- SIDEBAR: CONTROLS ---
st.sidebar.title("🎮 Control Panel")
run_mode = st.sidebar.radio("Mode", ["Manual Step", "Auto-Play (Fast)"])
step_btn = st.sidebar.button("👉 Run Next Turn")
reset_btn = st.sidebar.button("🔄 Reset Game")

# --- ANALYST AGENT (LLM) ---
st.sidebar.markdown("---")
st.sidebar.subheader("🎙️ Analyst Agent (Llama 3)")
if st.sidebar.button("📢 Generate Commentary"):
    if len(st.session_state.game_log) < 5:
        st.sidebar.warning("Not enough game history yet!")
    else:
        with st.sidebar.status("Analyst is thinking..."):
            # Summarize last 10 events
            recent_logs = st.session_state.game_log[-15:]
            prompt = f"""
            You are an Esports Commentator. Here is the recent action in a Monopoly AI Match:
            {recent_logs}
            
            Write a 2-sentence hype commentary on the current situation. 
            Focus on whoever is winning or making trades.
            """
            response = call_ollama(prompt)
            st.session_state.analyst_commentary = response

st.sidebar.info(st.session_state.analyst_commentary)

# --- MAIN LOGIC ---
if reset_btn:
    st.session_state.engine.reset(num_players=4)
    st.session_state.game_log = []
    st.session_state.turn_count = 0
    st.rerun()
def run_turn():
    engine = st.session_state.engine
    
    # 1. AI DECISION PHASE
    current_player = engine.players[engine.current_player_idx]
    
    # Encode state for the brain
    from ai.state_encoder import StateEncoder
    encoder = StateEncoder()
    state_vector = encoder.encode(current_player, engine.players, engine.board.spaces)
    
    # Ask the Brain
    brain_output = expert.predict(state_vector)
    
    # Store Brain Stats for UI
    st.session_state.last_brain_stats = brain_output
    
    # 2. EXECUTE ENGINE TURN
    log = engine.run_turn()
    st.session_state.turn_count += 1
    
    # --- ROBUST LOGGING FIX ---
    # Handle cases where 'player' or 'space' might be missing (e.g. Game Over)
    player_id = log.get('player', '?')
    space_name = log.get('space', 'Unknown')
    result_text = log.get('result', log.get('event', 'Event'))
    
    if log.get('event') == 'game_over':
        summary = f"Turn {st.session_state.turn_count}: 🏁 GAME OVER!"
    else:
        summary = f"Turn {st.session_state.turn_count}: P{player_id} landed on {space_name} ({result_text})"
    
    if log.get('trade_event'):
        summary += " [TRADE ATTEMPTED]"
        
    st.session_state.game_log.append(summary)

# Auto-Play Logic
if run_mode == "Auto-Play (Fast)" and step_btn:
    for _ in range(10): # Run 10 turns at once
        run_turn()
elif run_mode == "Manual Step" and step_btn:
    run_turn()

# --- UI LAYOUT ---
st.title("🎩 LucenFlow Monopoly: The Digital Twin")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📍 Live Board State")
    
    # Create a DataFrame for the board
    board_data = []
    players = st.session_state.engine.players
    
    # Simple ASCII-style list for now, or a metric grid
    for p in players:
        pos_name = st.session_state.engine.board.get_space(p.position)['name']
        board_data.append({
            "Player": f"Player {p.id}",
            "Position": pos_name,
            "Cash": f"£{p.cash}",
            "Net Worth": f"£{p.get_net_worth(st.session_state.engine.board)}",
            "Status": "JAIL" if p.in_jail else "Active"
        })
    
    st.dataframe(pd.DataFrame(board_data), hide_index=True)

    st.markdown("### 📜 Game Log")
    for line in reversed(st.session_state.game_log[-8:]):
        st.text(line)

with col2:
    st.subheader("🧠 Neural Network Live Feed")
    
    if 'last_brain_stats' in st.session_state:
        stats = st.session_state.last_brain_stats
        
        # 1. Recommendation
        rec = stats['recommendation']
        color = "green" if rec == "BUY" else "orange" if rec == "TRADE" else "grey"
        st.markdown(f"### Recommendation: :{color}[{rec}]")
        
        # 2. Confidence
        st.metric("Confidence Score", f"{stats['confidence_score']:.2f}")
        
        # 3. Q-Values Chart
        q_data = pd.DataFrame({
            "Action": list(stats['q_values'].keys()),
            "Value": list(stats['q_values'].values())
        })
        st.bar_chart(q_data, x="Action", y="Value", color="Action")
    else:
        st.info("Start the game to see Brain activity.")