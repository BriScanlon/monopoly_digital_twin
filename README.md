# 🎩 LucenFlow Monopoly Digital Twin

A Reinforcement Learning (RL) environment where an AI Agent learns to master the game of Monopoly. Moving beyond simple rules, this "Digital Twin" develops advanced strategies for **risk management**, **property valuation**, and **negotiation**.

## 🚀 Project Status: "Grandmaster" Level
The AI has evolved from a random bot to a strategic player. It currently implements:

1.  **Statistical Valuation (The Heatmap):** The AI knows that **Orange** properties are mathematically more valuable than **Green** ones due to the high frequency of players exiting Jail.
2.  **Liquidity Risk (The Panic Button):** The AI understands that *Cash is Survival*. It will refuse to buy properties—even valuable ones—if doing so drops its cash reserves into the "Danger Zone" (< £200).
3.  **Synergy Trading:** The AI actively identifies "Missing Links" (properties needed to complete a color set) and proposes trades to acquire them.
4.  **Defensive Blocking:** Opponents (and the AI) recognize "Kingmaker Trades." They will reject offers that give another player a Monopoly unless paid a massive premium (5x value).

---

## 🛠️ Project Structure

monopoly_digital_twin/
├── ai/
│   ├── rl_agent.py       # The Brain (Deep Q-Network)
│   ├── state_encoder.py  # The Eyes (Converts board state to 176 inputs)
│   └── trainer.py        # The Dojo (Training loop with advanced rewards)
├── core/
│   ├── engine.py         # The Physics (Game logic, trading rules, defensive checks)
│   └── player.py         # The Actor (Asset tracking, net worth calc)
├── dashboard/
│   └── app.py            # The Command Center (Streamlit visualization)
├── models/
│   └── monopoly_ai_trading.pth  # The Saved Brain
├── requirements.txt      # Dependencies
└── README.md
💻 Installation (Windows CPU)
This project is optimized for running on standard hardware (Intel/AMD CPUs) without requiring heavy GPU drivers.

1. Prerequisites
Python 3.11+

2. Setup Environment
PowerShell
# Create Virtual Environment
py -3.11 -m venv venv

# Activate (PowerShell)
.\venv\Scripts\Activate.ps1
3. Install Dependencies
Crucial: Install the CPU-only version of PyTorch first to save space and avoid errors.

PowerShell
# 1. Install PyTorch (CPU Version)
pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cpu](https://download.pytorch.org/whl/cpu)

# 2. Install Project Requirements
pip install -r requirements.txt
🎮 Usage
1. Train the AI
Run the training loop to teach the AI. It will play thousands of games against "Defensive Bots."

Watch for: 💰 AI MADE A DEAL! logs (rare but valuable).

Duration: ~20 minutes for 2000 episodes on a modern CPU.

PowerShell
python -m ai.trainer
2. Run the Dashboard
Visualize the AI's decision-making in real-time. Watch the Confidence Bars to see it choose between Pass, Buy, and Trade.

PowerShell
# Set path and run (PowerShell)
$env:PYTHONPATH = "."; streamlit run dashboard/app.py
🧠 AI Strategy Breakdown
The Input (State Encoder)
The AI sees the board as a vector of 176 numbers, including:

Self: Cash, Net Worth, Jail Status.

Opponents: Cash, Net Worth, Properties owned.

Board: For every property, it sees:

Ownership status.

Heatmap Score: A hardcoded probability multiplier (e.g., Orange = 1.2x, Green = 0.8x).

The Logic (Reward Function)
The AI is not just rewarded for winning; it is shaped by specific incentives:

Survival: +0.1 per turn alive.

Trade Success: +30.0 for completing a set.

Panic Penalty: -20.0 if Cash drops below £50 (teaches hoarding).

Bankruptcy: -500.0 (The ultimate failure).

The Trading Engine
When the AI chooses Action 2 (Trade):

It scans the board for a color group where it owns N-1 properties.

It identifies the owner of the missing card.

It calculates a "Fair Offer" (2.5x Market Price).

Defensive Check: The opponent checks if this trade will give the AI a Monopoly. If yes, the opponent demands a 5x Premium.

If the AI has enough cash to pay the premium, the deal is struck.
