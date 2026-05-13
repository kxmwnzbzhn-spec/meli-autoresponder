import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}"}
iid="MLM2910880749"
# Get item with all moderation fields
g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H).json()
print("Status:",g.get("status"),"Sub:",g.get("sub_status"))
print("Title:",g.get("title"))
print("Tags:",g.get("tags"))
# Moderation endpoint
mod=requests.get(f"https://api.mercadolibre.com/items/{iid}/moderations",headers=H)
print("\nMODERATIONS http=",mod.status_code)
print(mod.text[:2000])
# Try health endpoint
h=requests.get(f"https://api.mercadolibre.com/items/{iid}/health",headers=H)
print("\nHEALTH http=",h.status_code)
print(h.text[:1500])
