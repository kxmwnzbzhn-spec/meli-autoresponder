import os, requests
import meli_token
SRC="MLM5346655686"; API="https://api.mercadolibre.com"
WT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_WILBERT"]).json()["access_token"]
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
HW={"Authorization":f"Bearer {WT}"}
HA={"Authorization":f"Bearer {AT}"}; HAJ={**HA,"Content-Type":"application/json"}
s=requests.get(f"{API}/items/{SRC}",headers=HW,timeout=20).json()
sd=requests.get(f"{API}/items/{SRC}/description",headers=HW,timeout=15).json()
# subir cada foto del origen a la cuenta de Adrian -> map src_pic_id -> ah_pic_id
sess=requests.Session()
m={}; allah=[]
for p in (s.get("pictures") or []):
    sid=p.get("id"); url=p.get("secure_url") or p.get("url")
    if not (sid and url): continue
    img=sess.get(url,timeout=60).content
    rp=requests.post(f"{API}/pictures/items/upload",headers=HA,files={"file":("p.jpg",img,"image/jpeg")},timeout=120)
    if rp.status_code<300:
        ah=rp.json().get("id"); m[sid]=ah; allah.append(ah)
print("fotos subidas a Adrian:",len(allah))
# variaciones con sus fotos mapeadas
variations=[]
for v in (s.get("variations") or []):
    color=None
    for c in (v.get("attribute_combinations") or []):
        if c.get("id")=="COLOR" or c.get("name")=="Color": color=c.get("value_name")
    vp=[m[i] for i in (v.get("picture_ids") or []) if i in m]
    if not vp: vp=allah[:3]
    variations.append({"attribute_combinations":[{"id":"COLOR","value_name":color}],
                       "picture_ids":vp[:10],"available_quantity":1,"price":299})
payload={"site_id":"MLM","title":s.get("title"),"category_id":s.get("category_id"),
         "currency_id":"MXN","buying_mode":"buy_it_now","listing_type_id":s.get("listing_type_id") or "gold_special",
         "condition":s.get("condition") or "used",
         "pictures":[{"id":x} for x in allah],
         "attributes":[{"id":"BRAND","value_name":"Genérico"},{"id":"MODEL","value_name":"Genérico"}],
         "variations":variations}
print("variaciones:",[(vv["attribute_combinations"][0]["value_name"],len(vv["picture_ids"])) for vv in variations])
r=requests.post(f"{API}/items",headers=HAJ,json=payload,timeout=60)
print("publish http:",r.status_code)
if r.status_code>=300:
    print("body:",r.text[:1200]); print("DONE"); raise SystemExit(0)
nid=r.json().get("id"); print("NEW:",nid,"status:",r.json().get("status"))
orig=sd.get("plain_text") or ""
disc=("IMPORTANTE: El color se envia de forma ALEATORIA segun disponibilidad en almacen. "
      "NO se garantiza el envio de un color especifico.\n\n")
rd=requests.post(f"{API}/items/{nid}/description",headers=HAJ,json={"plain_text":disc+orig},timeout=30)
print("description http:",rd.status_code,"| PERMALINK:",r.json().get("permalink"))
print("DONE")
