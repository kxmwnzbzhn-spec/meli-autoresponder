"""Top vendidas Go 4 y Clip 5 en Raymundo (active + paused)."""
import os, requests, time
APP_ID="5211907102822632"
APP_SECRET=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_RAYMUNDO"]
r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":APP_ID,"client_secret":APP_SECRET,"refresh_token":RT}).json()
H={"Authorization":f"Bearer {r['access_token']}"}
me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
uid=me["id"]
print(f"Cuenta: {me['nickname']} ({uid})\n")

# Listar todos los items
all_iids=[]
for st in ["active","paused"]:
    offset=0
    while True:
        rr=requests.get(f"https://api.mercadolibre.com/users/{uid}/items/search?status={st}&limit=50&offset={offset}",headers=H,timeout=20).json()
        b=rr.get("results",[])
        if not b: break
        all_iids.extend(b); offset+=50
        if offset>=rr.get("paging",{}).get("total",0): break

print(f"Total items: {len(all_iids)}")

go4=[]; clip5=[]
for i in range(0,len(all_iids),20):
    chunk=all_iids[i:i+20]
    rr=requests.get("https://api.mercadolibre.com/items",headers=H,
                    params={"ids":",".join(chunk),"attributes":"id,title,price,status,sold_quantity"},
                    timeout=20).json()
    for resp in rr:
        if resp.get("code")!=200: continue
        it=resp.get("body")
        title=it.get("title","")
        tl=title.lower()
        sold=int(it.get("sold_quantity") or 0)
        entry={"iid":it["id"],"title":title[:60],"sold":sold,"price":it.get("price"),"status":it.get("status")}
        if "go 4" in tl or "go4" in tl: go4.append(entry)
        elif "clip 5" in tl or "clip5" in tl: clip5.append(entry)
    time.sleep(0.15)

go4.sort(key=lambda x:-x["sold"])
clip5.sort(key=lambda x:-x["sold"])

print(f"\n=== GO 4 — TOP {len(go4)} ===")
print(f"{'#':<3}{'IID':<16}{'sold':>6} {'$':>6} {'st':<8} title")
for i,e in enumerate(go4[:30],1):
    print(f"{i:<3}{e['iid']:<16}{e['sold']:>6} {str(e['price'] or ''):>6} {str(e['status'])[:7]:<8} {e['title'][:55]}")

print(f"\n=== CLIP 5 — TOP {len(clip5)} ===")
print(f"{'#':<3}{'IID':<16}{'sold':>6} {'$':>6} {'st':<8} title")
for i,e in enumerate(clip5[:30],1):
    print(f"{i:<3}{e['iid']:<16}{e['sold']:>6} {str(e['price'] or ''):>6} {str(e['status'])[:7]:<8} {e['title'][:55]}")
