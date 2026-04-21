import sys, os
sys.path.insert(0, '.')
from meli_autoresponder import refresh_access_token, handle_questions, load_state, save_json, STATE_FILE

state = load_state()
print("Getting token...")
tok = refresh_access_token()
print(f"Token OK: {tok[:20]}...")
print(f"Questions seen previously: {len(state.get('questions_seen',[]))}")

print("Running handle_questions...")
handle_questions(tok, state)
print("Done")

try:
    save_json(STATE_FILE, state)
    print(f"State saved: {len(state.get('questions_seen',[]))} questions")
except Exception as e:
    print(f"save err: {e}")
