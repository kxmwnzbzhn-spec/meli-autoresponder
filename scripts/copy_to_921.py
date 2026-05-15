import os,json,requests
RT=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json()["access_token"]
H={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

SRC="MLM5347901578"
DST="MLM2911241921"

# Get source pics + desc
src=requests.get(f"https://api.mercadolibre.com/items/{SRC}",headers=H).json()
src_pics=src.get("pictures",[])
pic_ids=[{"id":p.get("id")} for p in src_pics]
print(f"Source pics: {len(pic_ids)}")

src_desc=requests.get(f"https://api.mercadolibre.com/items/{SRC}/description",headers=H).json()
desc_text=src_desc.get("plain_text") or src_desc.get("text") or ""
print(f"Source desc len: {len(desc_text)}")

# Apply to destination
g=requests.get(f"https://api.mercadolibre.com/items/{DST}",headers=H).json()
print(f"\nDST BEFORE st={g.get('status')} price=${g.get('price')} pics={len(g.get('pictures',[]))}")

# Single PUT with pictures + price
body={"pictures":pic_ids,"price":799}
r=requests.put(f"https://api.mercadolibre.com/items/{DST}",headers=H,json=body)
print(f"UPDATE http={r.status_code} {r.text[:300]}")

# Description
d=requests.put(f"https://api.mercadolibre.com/items/{DST}/description",headers=H,json={"plain_text":desc_text})
if d.status_code>=300:
    d=requests.post(f"https://api.mercadolibre.com/items/{DST}/description",headers=H,json={"plain_text":desc_text})
print(f"DESC http={d.status_code} {d.text[:150]}")

# verify
g2=requests.get(f"https://api.mercadolibre.com/items/{DST}",headers=H).json()
print(f"\nDST AFTER st={g2.get('status')} price=${g2.get('price')} pics={len(g2.get('pictures',[]))} title={(g2.get('title') or '')[:60]}")
d2=requests.get(f"https://api.mercadolibre.com/items/{DST}/description",headers=H).json()
print(f"DST DESC len={len(d2.get('plain_text') or '')}")
