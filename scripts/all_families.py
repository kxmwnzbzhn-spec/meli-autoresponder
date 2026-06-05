"""Enumerate ALL JBL Go 4 CPIDs by walking COLOR pickers from every starting point."""
import os, requests, json, time
API="https://api.mercadolibre.com"
r=requests.post(f"{API}/oauth/token",data={
  "grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],
  "client_secret":os.environ["MELI_APP_SECRET"],
  "refresh_token":os.environ["MELI_REFRESH_TOKEN_CLARIBEL"]},timeout=20).json()
AT=r["access_token"]; H={"Authorization":f"Bearer {AT}"}

seeds=set()
for q in ["JBL Go 4","JBL Go4","Bocina JBL Go 4","Parlante JBL Go 4","JBL Go 4 azul","JBL Go 4 rojo"]:
    rr=requests.get(f"{API}/products/search",headers=H,
        params={"site_id":"MLM","status":"active","q":q,"limit":50},timeout=15)
    if rr.status_code==200:
        for it in (rr.json().get("results") or []):
            cpid=it.get("id")
            if cpid and cpid.startswith("MLM"): seeds.add(cpid)
print(f"Seed CPIDs: {len(seeds)}")

# For each seed, get color pickers -> add all siblings to universe
universe={}
visited=set()
for s in list(seeds)[:50]:
    if s in visited: continue
    visited.add(s)
    try:
        p=requests.get(f"{API}/products/{s}",headers=H,timeout=8).json()
    except: continue
    family=p.get("family_name") or ""
    if not ("go 4" in family.lower() or "go4" in family.lower().replace(" ","")): continue
    if any(x in family.lower() for x in ["go 3","essential","case","funda","pro"]): continue
    for pk in (p.get("pickers") or []):
        if pk.get("picker_id")=="COLOR":
            for prod in (pk.get("products") or []):
                pid=prod.get("product_id")
                if not pid: continue
                universe[pid]={
                    "color_label":prod.get("picker_label",""),
                    "name":prod.get("product_name",""),
                    "family":family,
                }
                visited.add(pid)
    time.sleep(0.1)

print(f"\nTotal Go 4 CPIDs found via family pickers: {len(universe)}")

# Group by family
families={}
for cpid,info in universe.items():
    families.setdefault(info["family"],[]).append((cpid,info["color_label"],info["name"]))

print(f"\nFamilies: {len(families)}")
for fam,prods in sorted(families.items(),key=lambda x:-len(x[1])):
    print(f"\n--- {fam} ({len(prods)} variants) ---")
    for cpid,label,name in prods:
        flag = " ★" if any(kw in label.lower() for kw in ["celeste","aqua","azul claro","light blue","turquesa","mint","menta","cielo","aquamarino","cyan","cian","turquoise"]) else ""
        print(f"  {cpid} | {label}{flag} | {name[:80]}")

# Filter just light blue family
print("\n\n=== ★ LIGHT BLUE FAMILY MATCHES ===")
matches=[]
for cpid,info in universe.items():
    if any(kw in info["color_label"].lower() for kw in ["celeste","aqua","azul claro","light blue","turquesa","mint","menta","cielo","aquamarino","cyan","cian","turquoise"]):
        # Also fetch aggregated sales
        try:
            p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=8).json()
            agg=p.get("aggregated_sales") or 0
            if not agg:
                bw=p.get("buy_box_winner") or {}
                agg=bw.get("sold_quantity") or 0
            price=(p.get("buy_box_winner") or {}).get("price")
            matches.append({"cpid":cpid,"color":info["color_label"],"name":info["name"],
                            "family":info["family"],"sales":agg,"price":price,
                            "link":p.get("permalink") or f"https://www.mercadolibre.com.mx/p/{cpid}"})
        except: pass
matches.sort(key=lambda x:-(x["sales"] or 0))
for m in matches:
    print(f"  sales={m['sales']:>5}  {m['cpid']}  | {m['color']:<25} | ${m['price']} | {m['name'][:60]}")
    print(f"    {m['link']}")
print("\nJSON:",json.dumps(matches,ensure_ascii=False))
