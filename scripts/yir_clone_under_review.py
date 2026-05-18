import os,requests,time
RT=os.environ["MELI_REFRESH_TOKEN_YC_NEW"]
CID=os.environ["MELI_APP_ID"]; CS=os.environ["MELI_APP_SECRET"]
T=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CS,"refresh_token":RT}).json().get("access_token")
H={"Authorization":f"Bearer {T}"}
HJ={"Authorization":f"Bearer {T}","Content-Type":"application/json"}

UNDER=["MLM2923681279","MLM5291788562","MLM5291786738","MLM5291786710","MLM5291786706","MLM5291776046","MLM5291774160","MLM5291772440","MLM5291772416","MLM2935587247","MLM2935587237","MLM2935447545","MLM2935447531","MLM2935286703","MLM2935286651","MLM2935286537","MLM5353056406","MLM5353056250","MLM2935286629","MLM2935286615","MLM2935286605","MLM2935286557","MLM2935298361"]

mapping=[]
errors=[]
for iid in UNDER:
    g=requests.get(f"https://api.mercadolibre.com/items/{iid}",headers=H,timeout=15).json()
    if not g.get("id"):
        errors.append((iid,"no data")); continue
    cpid=g.get("catalog_product_id")
    title=g.get("title"); cat=g.get("category_id")
    price=int(g.get("price") or 500)
    ltype=g.get("listing_type_id") or "gold_pro"
    body={
        "title":title,"category_id":cat,"price":price,"currency_id":"MXN",
        "available_quantity":1,"buying_mode":"buy_it_now","listing_type_id":ltype,
        "condition":g.get("condition","new"),
        "sale_terms":[{"id":"WARRANTY_TYPE","value_name":"Garantía del vendedor"},{"id":"WARRANTY_TIME","value_name":"30 días"}],
    }
    if cpid:
        body["catalog_listing"]=True
        body["catalog_product_id"]=cpid
    r=requests.post("https://api.mercadolibre.com/items",headers=HJ,json=body,timeout=20)
    if r.status_code<300:
        new=r.json().get("id")
        print(f"  ✓ {iid} → {new}  ({title[:40]} ${price})")
        mapping.append((iid,new))
    else:
        try:
            err=r.json()
            cause=err.get("cause",[{}])[0].get("code","?") if isinstance(err.get("cause"),list) and err.get("cause") else err.get("message","?")
        except: cause=r.text[:120]
        print(f"  ✗ {iid} http={r.status_code} cause={cause}")
        errors.append((iid,f"http={r.status_code} {cause}"))
    time.sleep(0.7)

print(f"\n=== {len(mapping)} cloned / {len(errors)} failed ===")
for old,new in mapping: print(f"  {old} → {new}")
print("\nERRORS:")
for i,e in errors[:10]: print(f"  {i}: {e}")
