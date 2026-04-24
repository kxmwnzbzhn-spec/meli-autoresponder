import os,requests,json
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
IID="MLM5241298820"
d=requests.get(f"https://api.mercadolibre.com/items/{IID}?include_attributes=all",headers=H).json()
print(f"TITLE: {d.get('title')}")
print("\nATTRS con 'jbl' o 'flip' o 'JBL':")
for a in (d.get("attributes") or []):
    v=(a.get("value_name","") or "").lower()
    if "jbl" in v or "flip" in v or "charge" in v or "clip" in v:
        print(f"  {a.get('id')}: {a.get('value_name')}")
print("\nTODOS los atributos:")
for a in (d.get("attributes") or []):
    print(f"  {a.get('id')}: {a.get('value_name')}")
desc=requests.get(f"https://api.mercadolibre.com/items/{IID}/description",headers=H).json().get("plain_text","")
print(f"\nDESC tiene 'JBL'? {'jbl' in desc.lower()}")
print(f"DESC tiene 'Flip'? {'flip' in desc.lower()}")
