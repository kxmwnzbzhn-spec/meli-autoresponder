import os, requests, json
import meli_token
SRC="MLM5346655686"; API="https://api.mercadolibre.com"
WT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_WILBERT"]).json()["access_token"]
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_AH"]).json()["access_token"]
HW={"Authorization":f"Bearer {WT}"}
HA={"Authorization":f"Bearer {AT}"}; HAJ={**HA,"Content-Type":"application/json"}
s=requests.get(f"{API}/items/{SRC}",headers=HW,timeout=20).json()
sd=requests.get(f"{API}/items/{SRC}/description",headers=HW,timeout=15).json()
pics=[{"source":p["url"]} for p in (s.get("pictures") or []) if p.get("url")]
colors=[]
for v in (s.get("variations") or []):
    for c in (v.get("attribute_combinations") or []):
        if (c.get("id")=="COLOR" or c.get("name")=="Color"): colors.append(c.get("value_name"))
colors=list(dict.fromkeys(colors))
GTINR=[{"id":"EMPTY_GTIN_REASON","value_id":"17055160"}]
variations=[{"attribute_combinations":[{"id":"COLOR","value_name":col}],
             "attributes":GTINR,"available_quantity":1,"price":299} for col in colors]
payload={"site_id":"MLM","title":s.get("title"),"category_id":s.get("category_id"),
         "currency_id":"MXN","buying_mode":"buy_it_now","listing_type_id":s.get("listing_type_id") or "gold_special",
         "condition":s.get("condition") or "used",
         "pictures":pics,
         "attributes":[{"id":"BRAND","value_name":"JBL"},{"id":"MODEL","value_name":"Go 4"}],
         "variations":variations}
print("colors:",colors,"| pics:",len(pics))
r=requests.post(f"{API}/items",headers=HAJ,json=payload,timeout=60)
print("publish http:",r.status_code)
if r.status_code>=300:
    print("body:",r.text[:600]); print("DONE"); raise SystemExit(0)
nid=r.json().get("id"); print("NEW:",nid,"status:",r.json().get("status"))
orig=sd.get("plain_text") or ""
disc=("IMPORTANTE: El color se envia de forma ALEATORIA segun disponibilidad en almacen. "
      "NO se garantiza el envio de un color especifico.\n\n")
rd=requests.post(f"{API}/items/{nid}/description",headers=HAJ,json={"plain_text":disc+orig},timeout=30)
print("description http:",rd.status_code)
print("PERMALINK:",r.json().get("permalink"))
print("DONE")
