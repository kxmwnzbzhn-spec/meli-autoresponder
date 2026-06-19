import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

CLAIM=5526369459  # ASVA vencido más viejo

# 1) Get claim full
r1=requests.get(f"{API}/post-purchase/v1/claims/{CLAIM}",headers=H,timeout=15).json()
print("=== CLAIM ===")
print(json.dumps({k:v for k,v in r1.items() if k not in ("messages","attachments")},indent=2,ensure_ascii=False)[:3000])

# 2) Get available actions / next steps
r2=requests.get(f"{API}/post-purchase/v1/claims/{CLAIM}/available-actions",headers=H,timeout=15)
print(f"\n=== AVAILABLE ACTIONS (status {r2.status_code}) ===")
print(r2.text[:1500])

# 3) Get expected resolutions
r3=requests.get(f"{API}/post-purchase/v1/claims/{CLAIM}/expected-resolutions",headers=H,timeout=15)
print(f"\n=== EXPECTED RESOLUTIONS (status {r3.status_code}) ===")
print(r3.text[:1500])

# 4) Get returns info
r4=requests.get(f"{API}/post-purchase/v1/claims/{CLAIM}/returns",headers=H,timeout=15)
print(f"\n=== RETURNS (status {r4.status_code}) ===")
print(r4.text[:1500])

# 5) Get messages
r5=requests.get(f"{API}/post-purchase/v1/claims/{CLAIM}/messages",headers=H,timeout=15)
print(f"\n=== MESSAGES (status {r5.status_code}) ===")
print(r5.text[:1500])
