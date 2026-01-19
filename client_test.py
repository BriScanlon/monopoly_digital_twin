import requests
import random
import json

# URL of your running API
API_URL = "http://localhost:8000/analyze/decision"

def generate_mock_state():
    """
    Generates a random vector of 205 floats to simulate a game state.
    In the real app, the StateEncoder would generate this from the live game.
    """
    # 205 is the exact input size expected by the model
    return [random.random() for _ in range(205)]

def test_expert():
    print("--- Testing Digital Expert API ---")
    
    # 1. Create the payload
    mock_vector = generate_mock_state()
    payload = {"state_vector": mock_vector}
    
    try:
        # 2. Send the POST request
        response = requests.post(API_URL, json=payload)
        
        # 3. Handle response
        if response.status_code == 200:
            data = response.json()
            print("\n✅ SUCCESS: API Responded")
            print(f"Recommendation: {data['decision']['recommendation']}")
            print(f"Confidence:     {data['decision']['confidence_score']:.4f}")
            print(f"Narrative:      {data['narrative']}")
            print("-" * 30)
            print("Full JSON:", json.dumps(data, indent=2))
        else:
            print(f"\n❌ ERROR: API returned status {response.status_code}")
            print(response.text)
            
    except requests.exceptions.ConnectionError:
        print("\n❌ CONNECTION ERROR: Is the API running? (python -m api.service)")

if __name__ == "__main__":
    test_expert()