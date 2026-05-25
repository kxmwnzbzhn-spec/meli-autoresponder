import os, json, requests, meli_token
API="https://api.mercadolibre.com"
AT=meli_token.refresh(os.environ["MELI_REFRESH_TOKEN_ASVA"])["access_token"]
H={"Authorization":f"Bearer {AT}"}
for iid in ["MLM2534863827","MLM2534876525"]:
    it=requests.get(f"{API}/items/{iid}",headers=H,timeout=15).json()
    print(f"\n=== {iid} ===")
    print("title:",it.get("title"))
    print("domain:",it.get("domain_id"),"cat:",it.get("category_id"),"price:",it.get("price"))
    print("pictures:",len(it.get("pictures") or []),"| variations:",len(it.get("variations") or []))
    print("ATRIBUTOS:")
    for a in it.get("attributes",[]):
        if a.get("value_name"): print(f"   [{a.get('id')}] {a.get('name')} = {a.get('value_name')}")
    # primeras pics
    for p in (it.get("pictures") or [])[:3]:
        print("   pic:",p.get("id"),p.get("secure_url","")[:70])
