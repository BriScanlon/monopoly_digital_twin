import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
from collections import deque

class MonopolyNet(nn.Module):
    def __init__(self, input_size, output_size):
        super(MonopolyNet, self).__init__()
        self.fc1 = nn.Linear(input_size, 128)
        self.fc2 = nn.Linear(128, 128)
        self.fc3 = nn.Linear(128, 64)
        self.fc4 = nn.Linear(64, output_size)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.relu(self.fc3(x))
        return self.fc4(x)

class Agent:
    def __init__(self, state_size, action_size, device=None):
        self.state_size = state_size
        self.action_size = action_size
        
        # Hyperparameters
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95    # discount rate
        self.epsilon = 1.0   # exploration rate
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995 # Placeholder, controlled externally
        self.learning_rate = 0.001
        
        # Device management
        if device:
            self.device = device
        else:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            
        self.model = MonopolyNet(state_size, action_size).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()

    def act(self, state):
        # Epsilon-greedy action selection
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)
        
        # Exploitation (Use Brain)
        # Convert state to tensor and move to GPU
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            act_values = self.model(state_tensor)
            
        return torch.argmax(act_values[0]).item()

    def train(self, state, action, reward, next_state, done):
        # Store in memory
        self.memory.append((state, action, reward, next_state, done))
        
        if len(self.memory) < 64:
            return

        # Mini-batch training
        minibatch = random.sample(self.memory, 32)
        
        # Prepare batches on GPU
        states = torch.FloatTensor(np.array([m[0] for m in minibatch])).to(self.device)
        actions = torch.LongTensor(np.array([m[1] for m in minibatch])).unsqueeze(1).to(self.device)
        rewards = torch.FloatTensor(np.array([m[2] for m in minibatch])).to(self.device)
        next_states = torch.FloatTensor(np.array([m[3] for m in minibatch])).to(self.device)
        dones = torch.FloatTensor(np.array([m[4] for m in minibatch])).to(self.device)

        # Predict Q values
        current_q = self.model(states).gather(1, actions).squeeze(1)
        
        # Target Q values
        next_q = self.model(next_states).max(1)[0]
        target_q = rewards + (self.gamma * next_q * (1 - dones))
        
        # Backprop
        loss = self.criterion(current_q, target_q.detach())
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # NOTE: No epsilon decay here! It is now handled in trainer.py
        
    def save(self, filename):
        torch.save(self.model.state_dict(), filename)