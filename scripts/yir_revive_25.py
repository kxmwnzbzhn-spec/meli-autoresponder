import os,requests,time,json
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json().get("access_token")
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

# Parse user IDs (dedup + handle concatenated)
RAW=["5291774150","5291785036","2923681279","5291788562","5291786738","5291786710","5291786706","5291776046",
     "5291774160","5291772440",
     "5291772416","2935587247",
     "2935587237","2935447545","2935447531","2935286703","2935286651","2935286537",
     "5353056406","5353056250","2935286629","2935286615","2935286605","2935286557","2935298361"]
ITEMS=list(dict.fromkeys("MLM"+x for x in RAW))
print(f"Total IDs to process: {len(ITEMS)}")

results={"activated":[],"cloned":[],"errors":[],"unchanged":[]}

for iid in ITEMS:
    print(f"\n{iid}")
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    if not g.get("id"):
        print(f"  ✗ no data: {str(g)[:150]}")
        results["errors"].append((iid,"no data"))
        continue
    st=g.get("status"); sub=g.get("sub_status",[]); qty=g.get("available_quantity",0)
    title=(g.get("title") or "")[:50]
    cpid=g.get("catalog_product_id")
    price=g.get("price",0) or 0
    print(f"  st={st} sub={sub} qty={qty} ${price} cpid={cpid}")
    print(f"  '{title}'")
    
    if st=="active":
        if qty==1:
            results["unchanged"].append(iid); continue
        r=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=15)
        print(f"  set qty=1 http={r.status_code}")
        results["activated"].append(iid)
    elif st=="paused":
        # Set qty=1 + active
        r1=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"available_quantity":1},timeout=15)
        time.sleep(0.3)
        r2=requests.put(f"https://api.mercadolibre.com/items/{iid}",headers=HJ,json={"status":"active"},timeout=15)
        print(f"  set qty=1 http={r1.status_code} | activate http={r2.status_code}")
        if r2.status_code<300:
            results["activated"].append(iid)
        else:
            print(f"    err: {r2.text[:200]}")
            results["errors"].append((iid,f"activate http={r2.status_code}"))
    elif st=="closed":
        # Try relist first
        r=requests.post(f"https://api.mercadolibre.com/items/{iid}/relist",headers=HJ,
                        json={"price":int(price) if price else 500,"quantity":1,"listing_type_id":g.get("listing_type_id") or "gold_pro"},timeout=15)
        print(f"  relist http={r.status_code} {r.text[:150]}")
        if r.status_code<300:
            new_id=r.json().get("id")
            print(f"  ✓ relisted as {new_id}")
            results["cloned"].append((iid,new_id))
        else:
            # Need to fully recreate via POST /items with same data
            cat=g.get("category_id")
            ltype=g.get("listing_type_id") or "gold_pro"
            body={
                "title":g.get("title"),"category_id":cat,"price":int(price) if price else 500,
                "currency_id":"MXN","available_quantity":1,"buying_mode":"buy_it_now",
                "listing_type_id":ltype,"condition":g.get("condition","new"),
                "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
            }
            if cpid:
                body["catalog_listing"]=True
                body["catalog_product_id"]=cpid
            r2=requests.post("https://api.mercadolibre.com/items",headers=HJ,json=body,timeout=20)
            if r2.status_code<300:
                new_id=r2.json().get("id")
                print(f"  ✓ recreated as {new_id}")
                results["cloned"].append((iid,new_id))
            else:
                print(f"  ✗ recreate http={r2.status_code} {r2.text[:300]}")
                results["errors"].append((iid,f"recreate http={r2.status_code}: {r2.text[:200]}"))
    else:
        results["errors"].append((iid,f"unknown status {st}"))
    time.sleep(0.6)

print("\n=== SUMMARY ===")
print(f"Activated: {len(results['activated'])}")
print(f"Cloned/Recreated: {len(results['cloned'])}")
print(f"Unchanged (already active qty=1): {len(results['unchanged'])}")
print(f"Errors: {len(results['errors'])}")
print("\n--- ACTIVATED ---")
for i in results["activated"]: print(f"  {i}")
print("\n--- CLONED ---")
for old,new in results["cloned"]: print(f"  {old} → {new}")
print("\n--- ERRORS ---")
for i,e in results["errors"]: print(f"  {i}: {e[:150]}")

# Output IDs to add to war
all_active=results["activated"]+[n for _,n in results["cloned"]]+results["unchanged"]
print(f"\n=== WAR_IDS ({len(all_active)}) ===")
print(",".join(all_active))
