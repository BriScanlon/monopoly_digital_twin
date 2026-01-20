Monopoly: Digital Twin & Analyst Agent
Monopoly, but with Neural learning.

Built along side Gemini Code.

It’s a proof-of-concept demonstrating how to combine a Simulation Engine, a Reinforcement Learning Agent, and a Local LLM Analyst into a single system.

I built this to test how autonomous agents negotiate, trade, and react to financial pressure in a closed environment.

🏗 The Architecture
The project is split into three distinct nodes:

The Engine (Simulation): A custom-built Python environment that enforces the strict rules of Monopoly (Auctions, Gaol, Housing shortages, etc.).

The Brain (RL Agent): A PyTorch-based Deep Q-Network (DQN).

Training: Trained over 2,000 episodes.

Behavior: It doesn't just play like an automated bot.  It understands asset value. It learned from scratch that trading is better than hoarding cash.

Hardware: Optimized for AMD GPUs (ROCm 6.1) on Linux.

The Analyst (Llama 3):

A local LLM running in a Docker container (Ollama).

It watches the game logs in real-time.

It generates "Sports Commentator" style narrative, analyzing strategies and roasting players who go bankrupt.

🚀 The Stack
Language: Python 3.11

ML Framework: PyTorch (ROCm backend for AMD 7900 XT support)

LLM Serving: Docker + Ollama (llama3 model)

Visualization: Streamlit (Real-time dashboard)

🛠 Setup & Installation
I developed this on Fedora Linux with an AMD GPU. If you are on NVIDIA or CPU, PyTorch should handle the fallback automatically, but the training times will vary.

1. Environment
Bash
# Clone and setup
git clone https://github.com/BriScanlon/monopoly_digital_twin.git
cd monopoly_digital_twin
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
(Note: If you are on AMD Linux, ensure you grab the ROCm version of PyTorch explicitly).

2. The Analyst (Docker)
You need Ollama running locally to handle the commentary.

Bash
docker run -d \
  --device /dev/kfd --device /dev/dri \
  -v ollama:/root/.ollama \
  -p 11434:11434 \
  --name ollama \
  ollama/ollama:rocm

# Pull the model
docker exec -it ollama ollama run llama3
🎮 Running the Digital Twin
1. Retrain the Brain (Optional)
If you want to create your own model from scratch:

Bash
python -m ai.trainer
Creates models/monopoly_ai_trading.pth

2. Launch the Dashboard
This brings up the visual interface where you can watch the AI play against itself and read the live analysis.

Bash
PYTHONPATH=. streamlit run dashboard/app.py
📊 Observations
Trading Logic: The agent attempts trades on ~65% of turns. It realised that "asking is free."

Validation: In a 500-game simulation, win rates were evenly distributed, proving the model is stable and not relying on first-mover advantage.
