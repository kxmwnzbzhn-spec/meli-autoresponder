import os,requests,json,time
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN"]}).json()
TOKEN=r["access_token"]
H={"Authorization":f"Bearer {TOKEN}","Content-Type":"application/json"}

FLIP7_IDS=["MLM2887818059","MLM2887824025"]
NEW_TITLE="Bocina Jbl Flip 7 Bluetooth Portatil Ip67 Bass 35w 16h Color"[:60]

# Primero intento update directo de title
print("=== INTENTO UPDATE TITLE DIRECTO ===")
need_republish=[]
for IID in FLIP7_IDS:
    rp=requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"title":NEW_TITLE},timeout=30)
    print(f"  {IID}: {rp.status_code}")
    if rp.status_code not in (200,201):
        print(f"    err: {rp.text[:300]}")
        need_republish.append(IID)

# Si fallo alguno, republicar: cerrar viejo + crear nuevo con mismo setup
if need_republish:
    print(f"\n=== REPUBLICAR {len(need_republish)} items ===")
    for IID in need_republish:
        cur=requests.get(f"https://api.mercadolibre.com/items/{IID}?include_attributes=all",headers=H).json()
        descr=requests.get(f"https://api.mercadolibre.com/items/{IID}/description",headers=H).json().get("plain_text","")
        print(f"\n  {IID}: cerrando...")
        requests.put(f"https://api.mercadolibre.com/items/{IID}",headers=H,json={"status":"closed"},timeout=20)
        
        # Limpiar atributos para reuso
        BAD={"EAN","UPC","MPN","SELLER_SKU","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","GRADING","LINE","DETAILED_MODEL","COLOR"}
        attrs=[]
        for a in (cur.get("attributes") or []):
            aid=a.get("id")
            if aid in BAD: continue
            val=a.get("value_name")
            if not val: continue
            if aid=="GTIN" and ("aplica" in val.lower() or len(val.replace(" ","").replace("-",""))<8):
                continue
            it={"id":aid,"value_name":val}
            if a.get("value_id"): it["value_id"]=str(a.get("value_id"))
            attrs.append(it)
        
        # Variations
        new_vars=[]
        for v in (cur.get("variations") or []):
            nv={
                "price":v.get("price"),
                "available_quantity":v.get("available_quantity"),
                "attribute_combinations":v.get("attribute_combinations",[]),
                "picture_ids":v.get("picture_ids") or [p.get("id") for p in (v.get("pictures") or [])],
            }
            v_attrs=[]
            for va in (v.get("attributes") or []):
                if va.get("id")=="GTIN" and va.get("value_name"):
                    v_attrs.append({"id":"GTIN","value_name":va.get("value_name")})
            if v_attrs: nv["attributes"]=v_attrs
            new_vars.append(nv)
        
        all_pics=[]
        for p in (cur.get("pictures") or []):
            pid=p.get("id")
            if pid and pid not in all_pics: all_pics.append(pid)
        
        body={
            "site_id":"MLM","title":NEW_TITLE,"category_id":cur.get("category_id"),
            "currency_id":"MXN",
            "listing_type_id":cur.get("listing_type_id","gold_special"),
            "condition":cur.get("condition","new"),"buying_mode":"buy_it_now",
            "sale_terms":[
                {"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},
                {"id":"WARRANTY_TIME","value_name":"30 días"},
            ],
            "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
            "pictures":[{"id":p} for p in all_pics],
            "attributes":attrs,
        }
        if new_vars:
            body["variations"]=new_vars
        else:
            body["price"]=399
            body["available_quantity"]=cur.get("available_quantity",10)
        
        rp=requests.post("https://api.mercadolibre.com/items",headers=H,json=body,timeout=60)
        print(f"    post nuevo: {rp.status_code}")
        if rp.status_code in (200,201):
            nid=rp.json()["id"]
            print(f"    *** NUEVO OK {nid} ***")
            if descr:
                rd=requests.put(f"https://api.mercadolibre.com/items/{nid}/description",headers=H,json={"plain_text":descr},timeout=20)
                print(f"    desc: {rd.status_code}")
        else:
            print(f"    err: {rp.text[:600]}")
