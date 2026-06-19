import os, requests, json
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_AH"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}

CID_CLAIM=5530747987  # AH Sony XB100 with refund_with_return

# Get the FULL claim object to see action structure
r1=requests.get(f"{API}/post-purchase/v1/claims/{CID_CLAIM}",headers=H,timeout=15).json()
print("=== FULL CLAIM ===")
print(json.dumps(r1,indent=2,ensure_ascii=False)[:5000])
