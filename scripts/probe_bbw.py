import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}

# Probar MLM46455780 = Charge 6 Roja catalog product
cpid="MLM46455780"
print(f"=== /products/{cpid} ===")
r=requests.get(f"https://api.mercadolibre.com/products/{cpid}",headers=H,timeout=15).json()
print(f"name: {r.get('name','')}")
print(f"buy_box_winner: {r.get('buy_box_winner')}")
print(f"buy_box: {r.get('buy_box')}")
print(f"children_ids: {len(r.get('children_ids',[]))}")
print(f"keys: {list(r.keys())}")

# Try /products/{id}/items
print(f"\n=== /products/{cpid}/items ===")
r2=requests.get(f"https://api.mercadolibre.com/products/{cpid}/items",headers=H,timeout=15).json()
print(json.dumps(r2,indent=1)[:2000])
