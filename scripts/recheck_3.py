import os, requests, json
r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
    "client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
}).json()
H = {"Authorization": f"Bearer {r['access_token']}"}

# También leer floor del catalog_war_state.json
state_url = "https://raw.githubusercontent.com/kxmwnzbzhn-spec/meli-autoresponder/main/data/catalog_war_state.json"
try:
    state = requests.get(state_url, timeout=5).json()
except:
    state = {}

ITEMS = ["MLM2891178657", "MLM2891178563", "MLM2891178603"]
for iid in ITEMS:
    print(f"\n=== {iid} ===")
    item = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H, timeout=10).json()
    cur = item.get("price"); status = item.get("status")
    print(f"  CURRENT precio:  ${cur} | status={status}/{item.get('sub_status')}")
    
    st_data = state.get("items", {}).get(iid, {})
    print(f"  state.json: original=${st_data.get('original_price','?')} floor_pct=?")
    
    # price_to_win actual
    ptw = requests.get(f"https://api.mercadolibre.com/items/{iid}/price_to_win?version=v2", headers=H, timeout=10).json()
    print(f"  PRICE_TO_WIN: {ptw.get('price_to_win')} | status={ptw.get('status')} | currentMELI={ptw.get('current_price')}")
    
    # Test: intentar bajar 1 peso para ver si la API acepta
    new_p = float(cur) - 1
    test = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers={**H, "Content-Type":"application/json"},
                       json={"price": new_p}, timeout=15)
    print(f"  TEST update -1 peso ({cur}→{new_p}): HTTP {test.status_code} {test.text[:200]}")
