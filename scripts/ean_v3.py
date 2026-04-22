import os,requests
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
H={"Authorization":f"Bearer {r['access_token']}","Content-Type":"application/json"}
IID="MLM2883448187"

EANS={"Negro":"6925281995194","Azul":"6925281995231","Rojo":"6925281995200","Camuflaje":"6925281995217","Rosa":"6925281995224","Aqua":"6925281995248"}

it=requests.get(f"https://api.mercadolibre.com/items/{IID}",headers=H,timeout=15).json()
current_vars=it.get("variations",[])

new_vars=[]
for v in current_vars:
    ac=v.get("attribute_combinations",[])
    color = ac[0].get("value_name","") if ac else ""
    ean=EANS.get(color)
    
    # GTIN va en "attributes" (no en attribute_combinations que es solo para variantes)
    nv={
        "id":v.get("id"),
        "price":v.get("price"),
        "available_quantity":v.get("available_quantity"),
        "attribute_combinations":[{"id":"COLOR","value_name":color}],
    }
    if ean:
        nv["attributes"]=[{"id":"GTIN","value_name":ean}]
    if v.get("picture_ids"): nv["picture_ids"]=v["picture_ids"]
    new_vars.append(nv)

# Pics top-level
all_var_pics=set()
for v in current_vars:
    for pid in (v.get("picture_ids") or []): all_var_pics.add(pid)
item_top_pics=[p.get("id") for p in it.get("pictures",[]) if p.get("id")]
all_pics=list(dict.fromkeys(list(all_var_pics)+item_top_pics))

body={"pictures":[{"id":p} for p in all_pics],"variations":new_vars}
r=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json=body,timeout=30)
print(f"PUT: {r.status_code}")
if r.status_code in (200,201):
    resp=r.json()
    print(f"\nVariaciones con GTIN:")
    for v in resp.get("variations",[]):
        ac=v.get("attribute_combinations",[])
        col = ac[0].get("value_name","") if ac else ""
        gtin=""
        for a in v.get("attributes",[]) or []:
            if a.get("id")=="GTIN": gtin=a.get("value_name","")
        print(f"  {v.get('id')} {col:<12} GTIN={gtin} qty={v.get('available_quantity')}")
else:
    print(r.text[:500])
