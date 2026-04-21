import sys, os
sys.path.insert(0, '.')
from meli_autoresponder import refresh_access_token, handle_questions, load_state, save_state

print("Loading state...")
try:
    state = load_state()
except:
    state = {}

print("Getting token...")
tok = refresh_access_token()
print(f"Token OK: {tok[:20]}...")

print("Running handle_questions...")
handle_questions(tok, state)
print("Done")

try: save_state(state)
except: pass
