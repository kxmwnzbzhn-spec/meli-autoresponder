import os,requests
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
IID="MLM2883448187"

# Estado actual
it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
print("=== Sale terms actuales ===")
for st in it.get("sale_terms",[]):
    print(f"  {st.get('id')}: {st.get('value_name')}")

# Fijar 30 dias garantia
new_terms=[
    {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
    {"id":"WARRANTY_TIME","value_name":"30 días"},
]
r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"sale_terms":new_terms},timeout=30)
print(f"\nPUT sale_terms: {r.status_code}")
if r.status_code in (200,201):
    for st in r.json().get("sale_terms",[]):
        print(f"  {st.get('id')}: {st.get('value_name')}")
else:
    print(r.text[:300])
