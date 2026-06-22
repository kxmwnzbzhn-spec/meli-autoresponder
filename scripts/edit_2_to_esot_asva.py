"""
EDIT (corregir) MLM52113823 y MLM69794978: cambiar dominio a MLM-ESOTERIC_PERFUMES
desde la cuenta ASVA (creadora original). No crear catálogos nuevos.
"""
import os, sys, json, hashlib, requests, time, re
sys.path.insert(0, "scripts")
import meli_token
API="https://api.mercadolibre.com"

CIDS=["MLM52113823","MLM69794978"]
AT=meli_token.get_access_token("ASVA")
H={"Authorization":f"Bearer {AT}"}; HJ={**H,"Content-Type":"application/json"}
me=requests.get(f"{API}/users/me",headers=H,timeout=15).json()
print("ASVA uid:", me.get("id"), "nick:", me.get("nickname"))

for cid in CIDS:
    print(f"\n========== EDIT {cid} → MLM-ESOTERIC_PERFUMES ==========")
    # 1) GET estado actual
    r=requests.get(f"{API}/products/{cid}",headers=H,timeout=15)
    if r.status_code!=200:
        print(f"  GET FAIL {r.status_code} {r.text[:120]}"); continue
    p=r.json()
    title=p.get("name","").strip()
    cur_dom=p.get("domain_id")
    cur_cat=p.get("category_id")
    print(f"  title: {title[:90]}")
    print(f"  current: dom={cur_dom} cat={cur_cat}")

    # 2) intentar payload de EDIT minimalista: solo cambio de dominio
    payload_simple={
        "site_id":"MLM",
        "type":"EDIT",
        "catalog_product_id":cid,
        "domain_id":"MLM-ESOTERIC_PERFUMES",
    }
    print(f"  → intento 1: EDIT solo dominio")
    rp=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=payload_simple,timeout=40)
    print(f"    POST {rp.status_code}")
    rb=rp.json();
    print(f"    body: {json.dumps(rb,ensure_ascii=False)[:500]}")
    sid=rb.get("id") or rb.get("suggestion_id")
    if sid:
        print(f"  >>> EDIT SID = {sid}  status={rb.get('status')}")
        continue

    # 3) payload completo con attrs + fotos re-subidas
    print(f"  → intento 2: EDIT con attrs + fotos")
    brand=""; model=""
    for a in p.get("attributes",[]):
        if a.get("id")=="BRAND": brand=(a.get("values") or [{}])[0].get("name","")
        if a.get("id")=="MODEL": model=(a.get("values") or [{}])[0].get("name","")
    if not brand: brand="The Alchemia Lab"
    if not model:
        mt=re.search(r"Perfume\s+(.+?)\s+The Alchemia Lab", title)
        model = (mt.group(1) if mt else "TAL") + " 100ml"
    ATTRS=[
     {"id":"BRAND","values":[{"name":brand}]},
     {"id":"MODEL","values":[{"name":model}]},
     {"id":"ITEM_CONDITION","values":[{"name":"Nuevo"}]},
    ]
    # re-upload fotos
    pics=[]
    for idx,pp in enumerate((p.get("pictures") or [])[:6]):
        u=pp.get("secure_url") or pp.get("url")
        if not u: continue
        try:
            img=requests.get(u,timeout=60).content
            rpi=requests.post(f"{API}/pictures/items/upload",headers=H,
                files={"file":(f"{cid}_{idx}.jpg",img,"image/jpeg")},timeout=120)
            if rpi.status_code in (200,201):
                pics.append({"id":rpi.json()["id"]})
            else:
                print(f"    pic[{idx}] upload {rpi.status_code}")
        except Exception as e:
            print(f"    pic[{idx}] err: {e}")
    print(f"    fotos:{len(pics)}")
    payload_attrs={
        "site_id":"MLM","type":"EDIT","catalog_product_id":cid,
        "domain_id":"MLM-ESOTERIC_PERFUMES","title":title,
        "attributes":ATTRS,"pictures":pics,
    }
    rp2=requests.post(f"{API}/catalog_suggestions",headers=HJ,json=payload_attrs,timeout=40)
    print(f"    POST {rp2.status_code}")
    rb2=rp2.json()
    print(f"    body: {json.dumps(rb2,ensure_ascii=False)[:600]}")
    sid2=rb2.get("id") or rb2.get("suggestion_id")
    if sid2:
        print(f"  >>> EDIT SID = {sid2}  status={rb2.get('status')}")
    time.sleep(2)
