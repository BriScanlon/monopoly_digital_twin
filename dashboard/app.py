import sys
import os
import streamlit as st
import pandas as pd
import torch

# --- PATH FIX ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.engine import MonopolyEngine
from core.player import Player
from ai.rl_agent import Agent
from ai.state_encoder import StateEncoder

# --- PAGE CONFIG ---
st.set_page_config(page_title="LucenFlow Monopoly Twin", layout="wide")
# Remove default top padding
st.markdown("""
    <style>
        .block-container {
            padding-top: 3rem;
            padding-bottom: 0rem;
        }
    </style>
""", unsafe_allow_html=True)

# --- CUSTOM ENGINE ---
class DashboardEngine(MonopolyEngine):
    def __init__(self):
        super().__init__()
        self.ai_decision = 1 # Default to Buy

    def set_ai_decision(self, action):
        self.ai_decision = action

    def _handle_property(self, player, space, log):
        if space['owner'] is None:
            can_afford = player.cash > space['price']
            wants_to_buy = (self.ai_decision == 1)
            
            if can_afford and wants_to_buy:
                player.buy_property(space)
                space['owner'] = player.id
                log['result'] = "bought_property"
            else:
                log['result'] = "pass_choice" if can_afford else "pass_no_money"
        elif space['owner'] != player.id:
            rent = space['rent']
            amount = player.pay(rent)
            self.players[space['owner']].receive(amount)
            log['result'] = f"paid_rent_{amount}"
        else:
            log['result'] = "already_owned"

# --- INITIALIZATION ---
if 'engine' not in st.session_state:
    st.session_state.engine = DashboardEngine()
    st.session_state.game_log = []
    st.session_state.turn_count = 0
    st.session_state.ai_stats = {"decisions": [], "net_worth": []}

    device = torch.device("cpu")
    agent = Agent(state_size=176, action_size=3, device=device)
    
    model_path = os.path.join(os.path.dirname(__file__), '../models/monopoly_ai_trading.pth')
    if os.path.exists(model_path):
        try:
            agent.model.load_state_dict(torch.load(model_path, map_location=device))
            st.session_state.agent = agent
        except Exception as e:
            st.error(f"Model load failed: {e}")
    else:
        st.session_state.agent = agent

    st.session_state.encoder = StateEncoder()

# --- LOGIC ---
def run_turn():
    engine = st.session_state.engine
    agent = st.session_state.agent
    encoder = st.session_state.encoder
    
    current_player = engine.players[engine.current_player_idx]
    state = encoder.encode(current_player, engine.players, engine.board.spaces)
    
    # AI Decision
    if current_player.id == 0:
        action = agent.act(state)
        with torch.no_grad():
            state_t = torch.FloatTensor(state).unsqueeze(0).to(agent.device)
            q_values = agent.model(state_t).cpu().numpy()[0]
        st.session_state.last_q_values = q_values
        st.session_state.last_action = action
    else:
        action = 1
        st.session_state.last_action = None

    engine.set_ai_decision(action)
    log = engine.run_turn()
    
    # Trade Logic
    trade_msg = ""
    if current_player.id == 0 and action == 2:
        success, msg = engine.try_smart_trade(current_player.id)
        if success:
            trade_msg = f" [TRADE: {msg}]"
            log['trade_event'] = True

    # Logging
    st.session_state.turn_count += 1
    player_label = f"P{log.get('player', '?')}"
    space_name = log.get('space', 'Unknown')
    result_text = log.get('result', log.get('event', 'Event'))
    summary = f"T{st.session_state.turn_count}: {player_label} @ {space_name} ({result_text}){trade_msg}"
    st.session_state.game_log.insert(0, summary)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎮 Controls")
    if st.button("Run Turn", type="primary", use_container_width=True):
        run_turn()
    if st.button("Reset Game", use_container_width=True):
        st.session_state.engine = DashboardEngine()
        st.session_state.game_log = []
        st.session_state.turn_count = 0
        st.rerun()

# --- MAIN LAYOUT (3 COLUMNS) ---
col_board, col_brain, col_log = st.columns([2, 1.2, 1])

# COLUMN 1: BOARD
with col_board:
    st.subheader("📍 Board State")
    board_data = []
    for s in st.session_state.engine.board.spaces:
        owner = f"P{s['owner']}" if s['owner'] is not None else "-"
        # Simplified Color Logic for display
        color = s.get('group', 'Special') 
        if color is None: color = "Special"
        
        board_data.append({
            "Space": s['name'],
            "Grp": color,
            "Cost": s.get('price', 0),
            "Own": owner,
            "Rent": s.get('rent', 0)
        })
    df = pd.DataFrame(board_data)
    # Taller board, scannable
    st.dataframe(df, height=600, use_container_width=True, hide_index=True)

# COLUMN 2: BRAIN
with col_brain:
    st.subheader("🧠 AI Brain (P0)")
    p0 = st.session_state.engine.players[0]
    
    # Compact Metrics
    c1, c2 = st.columns(2)
    c1.metric("Cash", f"£{p0.cash}")
    c2.metric("Net Worth", f"£{p0.get_net_worth_raw()}")
    
    st.divider()
    
    # Decision Chart
    if hasattr(st.session_state, 'last_q_values'):
        q = st.session_state.last_q_values
        actions = ["Pass", "Buy", "Trade"]
        
        # Safe Action Display
        chosen_idx = st.session_state.get('last_action')
        if chosen_idx is not None:
            st.success(f"Action: **{actions[chosen_idx]}**")
        else:
            st.info("Waiting for AI...")
            
        chart_data = pd.DataFrame({"Action": actions, "Value": q})
        st.bar_chart(chart_data, x="Action", y="Value", height=200)

    # Property List (Collapsible)
    with st.expander(f"Portfolio ({len(p0.properties)})", expanded=True):
        if p0.properties:
            for p in p0.properties:
                st.caption(f"🏠 {p['name']} ({p['group']})")
        else:
            st.caption("No Assets")

# COLUMN 3: LOGS
with col_log:
    st.subheader("📜 Event Log")
    # Join logs into a single string for text_area
    log_text = "\n".join(st.session_state.game_log)
    st.text_area("History", value=log_text, height=600, label_visibility="collapsed")