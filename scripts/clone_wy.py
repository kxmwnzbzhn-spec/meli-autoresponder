import os, requests
import meli_token
SRC="MLM2956944279"; API="https://api.mercadolibre.com"
WT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_WILBERT"]).json()["access_token"]
YT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_YC_NEW"]).json()["access_token"]
HW={"Authorization":f"Bearer {WT}"}
HY={"Authorization":f"Bearer {YT}"}; HYJ={**HY,"Content-Type":"application/json"}
s=requests.get(f"{API}/items/{SRC}",headers=HW,timeout=20).json()
sd=requests.get(f"{API}/items/{SRC}/description",headers=HW,timeout=15).json()
sess=requests.Session(); allah=[]
src_map={}
for ip,p in enumerate(s.get("pictures") or []):
    url=p.get("secure_url") or p.get("url")
    if not url: continue
    img=sess.get(url,timeout=60).content
    rp=requests.post(f"{API}/pictures/items/upload",headers=HY,files={"file":("p.jpg",img,"image/jpeg")},timeout=120)
    if rp.status_code<300:
        ah=rp.json().get("id"); allah.append(ah)
        if p.get("id"): src_map[p["id"]]=ah
print("pics subidas a Yiriam:",len(allah))
# variaciones con su mapeo de fotos por color
variations=[]
for v in (s.get("variations") or []):
    color=None
    for c in (v.get("attribute_combinations") or []):
        if c.get("id")=="COLOR" or c.get("name")=="Color": color=c.get("value_name")
    vp=[src_map[i] for i in (v.get("picture_ids") or []) if i in src_map]
    if not vp: vp=allah[:3]
    qty=v.get("available_quantity") or 1
    variations.append({"attribute_combinations":[{"id":"COLOR","value_name":color}],
                       "picture_ids":vp[:10],"available_quantity":qty,"price":v.get("price") or 299})
print("variaciones:",[(vv["attribute_combinations"][0]["value_name"],vv["available_quantity"]) for vv in variations])
payload={"site_id":"MLM","title":s.get("title"),"category_id":s.get("category_id"),
         "currency_id":"MXN","buying_mode":"buy_it_now","listing_type_id":s.get("listing_type_id") or "gold_special",
         "condition":s.get("condition") or "used",
         "pictures":[{"id":x} for x in allah],
         "attributes":[{"id":"BRAND","value_name":"Genérico"},{"id":"MODEL","value_name":"Genérico"}],
         "variations":variations}
r=requests.post(f"{API}/items",headers=HYJ,json=payload,timeout=60)
print("publish http:",r.status_code)
if r.status_code>=300:
    print("body:",r.text[:600]); raise SystemExit(0)
nid=r.json().get("id")
print("NEW:",nid,"status:",r.json().get("status"))
# descripcion: reusar la del Wilbert (random color)
desc=sd.get("plain_text") or ""
rd=requests.put(f"{API}/items/{nid}/description",headers=HYJ,json={"plain_text":desc},timeout=30)
print("description http:",rd.status_code,"| PERMALINK:",r.json().get("permalink"))
print("DONE")
