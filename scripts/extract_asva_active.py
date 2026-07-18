import os, requests, json, csv
APP_ID=os.environ["MELI_APP_ID"]; APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post("https://api.mercadolibre.com/oauth/token",
  data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT},timeout=25).json()
AT=r["access_token"]
print(f"NEW_RT_ASVA: {r['refresh_token']}",flush=True)
H={"Authorization":f"Bearer {AT}"}
USER_ID=1668713481

# Fetch all item IDs — filter by active status
all_ids=[]
offset=0
while True:
    r=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=50&offset={offset}",headers=H,timeout=15).json()
    ids=r.get("results",[])
    if not ids: break
    all_ids.extend(ids)
    if len(ids)<50: break
    offset+=50

print(f"Total ACTIVE ASVA items: {len(all_ids)}",flush=True)

# Fetch full details in batches
items=[]
for i in range(0, len(all_ids), 20):
    batch=all_ids[i:i+20]
    r=requests.get(f"https://api.mercadolibre.com/items?ids={','.join(batch)}&attributes=id,title,catalog_product_id,category_id,price,available_quantity,attributes",headers=H,timeout=20).json()
    for entry in r:
        b=entry.get("body",{})
        # Extract brand + model from attributes
        brand=""; model=""; ean=""
        for a in b.get("attributes",[]):
            aid=a.get("id","")
            if aid=="BRAND": brand=a.get("value_name","") or ""
            elif aid=="MODEL": model=a.get("value_name","") or ""
            elif aid in ("EAN","GTIN"): ean=a.get("value_name","") or ""
        items.append({
            "id":b.get("id"),
            "title":b.get("title",""),
            "cpid":b.get("catalog_product_id") or "",
            "cat":b.get("category_id",""),
            "brand":brand,
            "model":model,
            "ean":ean,
            "price":b.get("price",0),
            "qty":b.get("available_quantity",0),
        })

# Save as CSV to /tmp then upload to workflow output
import csv, io
buf=io.StringIO()
w=csv.DictWriter(buf, fieldnames=["id","title","cpid","cat","brand","model","ean","price","qty"])
w.writeheader()
for it in items: w.writerow(it)
csv_content=buf.getvalue()

# Also save to file we can retrieve via workflow artifact
with open("/tmp/asva_active.csv","w") as f: f.write(csv_content)
print("=== CSV OUTPUT ===",flush=True)
print(csv_content,flush=True)
