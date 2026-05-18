import os,json,requests,time
RT_W=os.environ["MELI_REFRESH_TOKEN_WILBERT"]
RT_D=os.environ["MELI_REFRESH_TOKEN_DILCIE"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]

def tok(rt):
    return requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":rt},timeout=15).json().get("access_token")

TW=tok(RT_W); TD=tok(RT_D)
if not TD:
    print("ERR: Dilcie token failed"); raise SystemExit(1)
HW={"Authorization":f"Bearer {TW}"}
HD={"Authorization":f"Bearer {TD}","Content-Type":"application/json"}

# Verify Dilcie account is active
me=requests.get("https://api.mercadolibre.com/users/me",headers={"Authorization":f"Bearer {TD}"}).json()
print(f"Dilcie status: uid={me.get('id')} nick={me.get('nickname')} site={me.get('site_id')}")
if not me.get("id"):
    print(f"ERR Dilcie not active: {me}"); raise SystemExit(1)

def upload_pic(t,u):
    img=requests.get(u,timeout=20)
    if img.status_code!=200: return None
    files={"file":("p.jpg",img.content,"image/jpeg")}
    r=requests.post("https://api.mercadolibre.com/pictures/items/upload",headers={"Authorization":f"Bearer {t}"},files=files)
    return r.json().get("id") if r.status_code<300 else None

ITEMS=["MLM2910806845","MLM2914422351","MLM2910768325","MLM2910806881","MLM2910457917",
       "MLM2910768333","MLM2910768335","MLM2910806871","MLM2910768369","MLM5351937060",
       "MLM5354755946","MLM5297098664","MLM2931341689","MLM5297087174","MLM2931612609",
       "MLM2931612611","MLM2937969761","MLM5337919270","MLM5337919290"]

results=[]
batch_size=5
for batch_idx in range(0, len(ITEMS), batch_size):
    batch=ITEMS[batch_idx:batch_idx+batch_size]
    print(f"\n=== BATCH {batch_idx//batch_size+1} (items {batch_idx+1}-{batch_idx+len(batch)}) ===")
    for wb_id in batch:
        try:
            g=requests.get(f"https://api.mercadolibre.com/items/{wb_id}",headers=HW,timeout=15).json()
            title=g.get("title","")
            cat=g.get("category_id")
            cpid=g.get("catalog_product_id")
            price=int(g.get("price",0))
            cond=g.get("condition","new")
            ltype=g.get("listing_type_id") or "gold_pro"
            pics=[(p.get("url") or p.get("secure_url")) for p in (g.get("pictures") or [])][:8]
            print(f"\n  {wb_id} '{title[:50]}' ${price} cpid={cpid} cond={cond}")
            
            body={
                "title":title,"category_id":cat,"price":price,"currency_id":"MXN",
                "available_quantity":g.get("available_quantity",1) or 1,
                "buying_mode":"buy_it_now","listing_type_id":ltype,"condition":cond,
                "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"90 días"}],
            }
            if cpid:
                body["catalog_listing"]=True
                body["catalog_product_id"]=cpid
            else:
                # tradicional - upload pics
                pic_ids=[]
                for u in pics:
                    pid=upload_pic(TD,u)
                    if pid: pic_ids.append(pid)
                if pic_ids: body["pictures"]=[{"id":p} for p in pic_ids]
                body["shipping"]={"mode":"me2","local_pick_up":False,"free_shipping":True,"logistic_type":"drop_off"}
            r=requests.post("https://api.mercadolibre.com/items",headers=HD,json=body,timeout=30)
            if r.status_code<300:
                new=r.json()
                nid=new.get("id")
                print(f"    ✓ NEW_ID={nid} ${new.get('price')} {new.get('status')}")
                results.append({"src":wb_id,"new":nid,"price":price,"title":title[:40]})
            else:
                err=r.json() if r.text.startswith("{") else {"e":r.text[:200]}
                cause=err.get("cause",[{}])[0].get("code") if isinstance(err.get("cause"),list) and err.get("cause") else err.get("message","?")
                print(f"    ✗ http={r.status_code} cause={cause}")
                results.append({"src":wb_id,"err":str(cause)[:200],"http":r.status_code})
        except Exception as e:
            print(f"    ✗ exception: {e}")
            results.append({"src":wb_id,"err":str(e)[:150]})
        time.sleep(0.8)
    # Sleep between batches
    if batch_idx+batch_size<len(ITEMS):
        print(f"  --- sleeping 3s antes de siguiente batch ---")
        time.sleep(3)

print("\n=== SUMMARY ===")
ok=[r for r in results if r.get("new")]
err=[r for r in results if r.get("err")]
print(f"OK: {len(ok)}/{len(results)}  ERR: {len(err)}")
for r in results:
    if r.get("new"):
        print(f"  ✓ {r['src']} → {r['new']} ${r['price']}")
    else:
        print(f"  ✗ {r['src']}: {r.get('err','?')[:80]}")
