import os, requests, json, sys, time
APP_ID = "5211907102822632"
APP_SECRET = os.getenv("MELI_APP_SECRET","")
RT = os.getenv("MELI_REFRESH_TOKEN","")

ITEMS = ["MLM2890793859", "MLM2890818973", "MLM2890793871", "MLM2890856611"]

r = requests.post("https://api.mercadolibre.com/oauth/token", data={
    "grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT
})
at = r.json()["access_token"]
H = {"Authorization":f"Bearer {at}", "Content-Type":"application/json"}

print("Setting visible=1 on 4 catalog items...")
for iid in ITEMS:
    g = requests.get(f"https://api.mercadolibre.com/items/{iid}", headers=H).json()
    cur = g.get("available_quantity", 0)
    status = g.get("status","")
    title = g.get("title","")[:50]
    if status != "active":
        print(f"  {iid} [{title}] status={status} → skip (real_stock=15 ya está en bot)")
        continue
    rp = requests.put(f"https://api.mercadolibre.com/items/{iid}", headers=H,
                     json={"available_quantity": 1})
    new = rp.json().get("available_quantity") if rp.status_code==200 else "?"
    print(f"  {iid} [{title}] visible {cur} → {new} ({rp.status_code})")
    time.sleep(1)
print("Done")
