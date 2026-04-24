import os,requests,json,time

ITEMS=["MLM5226013726","MLM5226014888"]

ACCOUNTS={
    "CLARIBEL":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"],
    "JUAN":os.environ["MELI_REFRESH_TOKEN"],
    "ASVA":os.environ["MELI_REFRESH_TOKEN_ASVA"],
    "RAYMUNDO":os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"],
}

# Token Claribel para publicar
rc=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]}).json()
TOK_C=rc["access_token"]
HC={"Authorization":f"Bearer {TOK_C}","Content-Type":"application/json"}

# Tokens para lectura
TOKENS={}
for label,rt in ACCOUNTS.items():
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()
    if "access_token" in r: TOKENS[label]=r["access_token"]

def reup(pid):
    try:
        img=requests.get(f"https://http2.mlstatic.com/D_{pid}-O.jpg",timeout=15).content
        if len(img)<2000: return None
        rp=requests.post("https://api.mercadolibre.com/pictures/items/upload",
            headers={"Authorization":f"Bearer {TOK_C}"},
            files={"file":("p.jpg",img,"image/jpeg")},timeout=45)
        return rp.json().get("id") if rp.status_code in (200,201) else None
    except: return None

BAD_ATTR={"EAN","UPC","MPN","SELLER_SKU","IS_SMART","PACKAGE_LENGTH","PACKAGE_WIDTH","PACKAGE_HEIGHT","PACKAGE_WEIGHT","LENGTH","WIDTH","HEIGHT","WEIGHT","ALPHANUMERIC_MODEL","GRADING","LINE","DETAILED_MODEL"}

for iid in ITEMS:
    # Buscar item
    d=None
    for label,t in TOKENS.items():
        H={"Authorization":f"Bearer {t}"}
        r=requests.get(f"https://api.mercadolibre.com/items/{iid}?include_attributes=all",headers=H,timeout=15).json()
        if r.get("id")==iid:
            d=r
            desc_r=requests.get(f"https://api.mercadolibre.com/items/{iid}/description",headers=H,timeout=10).json()
            desc=desc_r.get("plain_text","")
            break
    if not d:
        print(f"{iid}: NOT FOUND")
        continue
    
    print(f"\n=== {iid} '{d.get('title','')[:50]}' ===")
    
    # Pics
    pics_src=[p.get("id") for p in (d.get("pictures") or [])][:8]
    new_pics=[]
    for p in pics_src:
        n=reup(p)
        if n: new_pics.append(n)
    print(f"  pics: {len(new_pics)}")
    
    # Atributos limpios - usar value_id cuando disponible
    attrs=[]
    IGNORED={"IS_HIGHLIGHT_BRAND","IS_TOM_BRAND"}
    for a in (d.get("attributes") or []):
        aid=a.get("id")
        if aid in BAD_ATTR or aid in IGNORED: continue
        val_name=a.get("value_name","")
        val_id=a.get("value_id")
        if not val_name and a.get("values"):
            val_name=(a.get("values") or [{}])[0].get("name","")
            val_id=val_id or (a.get("values") or [{}])[0].get("id")
        if not val_name: continue
        item_attr={"id":aid,"value_name":val_name}
        if val_id:
            item_attr["value_id"]=str(val_id)
        attrs.append(item_attr)
    
    # Sale terms: SKIP PURCHASE_MAX_QUANTITY porque MELI no permite modificarlo
    sale_terms=[st for st in (d.get("sale_terms") or []) if st.get("id") not in ("PURCHASE_MAX_QUANTITY","MAX_UNITS_PER_BUYER")]
    
    body={
        "site_id":"MLM",
        "title":d.get("title"),
        "category_id":d.get("category_id"),
        "currency_id":d.get("currency_id","MXN"),
        "price":d.get("price"),
        "available_quantity":d.get("available_quantity",10),
        "listing_type_id":d.get("listing_type_id","gold_special"),
        "condition":d.get("condition"),
        "buying_mode":"buy_it_now",
        "sale_terms":sale_terms,
        "shipping":{"mode":"me2","local_pick_up":False,"free_shipping":True,"free_methods":[]},
        "pictures":[{"id":p} for p in new_pics],
        "attributes":attrs,
    }
    
    rp=requests.post("https://api.mercadolibre.com/items",headers=HC,json=body,timeout=60)
    print(f"  status: {rp.status_code}")
    if rp.status_code in (200,201):
        new_id=rp.json()["id"]
        print(f"  *** OK {new_id} ***")
        if desc:
            rd=requests.put(f"https://api.mercadolibre.com/items/{new_id}/description",headers=HC,json={"plain_text":desc},timeout=20)
            print(f"  desc: {rd.status_code}")
    else:
        print(f"  err: {rp.text[:1200]}")
    time.sleep(2)
