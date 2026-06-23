import os,requests,json,re
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
UA={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15"}

# Aggressive multi-query exhaustive search for JBL Go 4 Rosa CPIDs
queries=["JBL Go 4 Rosa","JBL Go 4 Rosado","Bocina JBL Go 4 Rosa","Parlante JBL Go 4 Rosa","Altavoz JBL Go 4 Rosa","JBL Go4 Rosa","JBL GO 4 pink","Dzyp JBL Go 4","Impermeable Polvo Go 4","Bluetooth Jbl Go 4 rosa"]
all_cpids={}
for q in queries:
  for offset in (0,10,20,30,40):
    url=f"{API}/products/search?q={q.replace(' ','%20')}&site_id=MLM&offset={offset}&limit=10&status=active"
    try: r=requests.get(url,headers=H,timeout=15)
    except: break
    if r.status_code!=200: break
    res=r.json().get("results",[])
    if not res: break
    for it in res:
      cpid=it.get("id") or it.get("catalog_product_id")
      name=(it.get("name") or "").lower()
      # must contain Go 4 + (rosa/pink/rosado/chicle)
      if not ("go 4" in name or "go4" in name): continue
      if not re.search(r"\b(rosa|rosado|pink|chicle|rojo)\b",name): continue
      # exclude accessories
      if any(x in name for x in ["case","funda","estuche","protec","silicona","cover","correa","eva"]): continue
      if cpid not in all_cpids:
        all_cpids[cpid]={"name":it.get("name")}

print(f"Total Rosa CPIDs encontrados: {len(all_cpids)}")

# Enrich each with full info + scrape catalog page for "vendidos"
RESULTS=[]
for cpid in all_cpids:
  p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=10).json()
  if p.get("status")!="active": continue
  
  color=None; brand=None
  for a in (p.get("attributes") or []):
    if a.get("id") in ("COLOR","MAIN_COLOR") and not color: color=a.get("value_name")
    if a.get("id")=="BRAND" and not brand: brand=a.get("value_name")
  if brand and brand.upper()!="JBL": continue
  
  bbw=p.get("buy_box_winner") or {}
  price=bbw.get("price")
  
  # Items count + child item IDs
  it=requests.get(f"{API}/products/{cpid}/items?limit=50",headers=H,timeout=10).json()
  items_total=it.get("paging",{}).get("total",0)
  items=it.get("results",[])
  iids=[i.get("item_id") for i in items[:15] if i.get("item_id")]
  
  # Visits
  visits=0
  if iids:
    v=requests.get(f"{API}/visits/items?ids={','.join(iids)}",headers=H,timeout=10)
    if v.status_code==200: visits=sum((v.json() or {}).values())
  
  # Reviews
  reviews=0
  for iid in iids[:8]:
    try:
      rv=requests.get(f"{API}/reviews/item/{iid}",headers=H,timeout=6).json()
      reviews+=rv.get("paging",{}).get("total",0)
    except: pass
  
  # HTML scrape sin-mobile (cleaner HTML)
  vendidos_html=None
  for u in [f"https://www.mercadolibre.com.mx/p/{cpid}",
            f"https://articulo.mercadolibre.com.mx/{cpid.replace('MLM','MLM-')}"]:
    try:
      hh=requests.get(u,headers=UA,timeout=12,allow_redirects=True)
      if hh.status_code!=200: continue
      # Search for sold patterns - multiple variants used by MELI frontend
      for pat in [r'(\d+(?:[.,]\d+)?\s*[kK]?\+?\s*vendidos?)',
                  r'"sold_quantity"\s*:\s*(\d+)',
                  r'sold_quantity\\?":\s*(\d+)',
                  r'\\u002Fvendidos[^"]*?(\d+)',
                  r'>\s*(\d+(?:[.,]\d+)?\s*[kK]?\+?\s*vendidos?)\s*<']:
        m=re.search(pat,hh.text)
        if m:
          vendidos_html=m.group(1); break
      if vendidos_html: break
    except: pass
  
  RESULTS.append({
    "cpid":cpid,"color":color,"name":p.get("name","")[:80],
    "ventas_HTML":vendidos_html,
    "items":items_total,"visits":visits,"reviews":reviews,
    "price":price,
    "url":f"https://www.mercadolibre.com.mx/p/{cpid}"
  })

# Composite score: reviews + visits/10 + items*2 (sellers competing)
for r in RESULTS:
  r["score"]=(r["reviews"] or 0)+(r["visits"] or 0)//10+(r["items"] or 0)*2

RESULTS.sort(key=lambda x:-x["score"])
print(f"\n=== JBL GO 4 ROSA — RANKING POR VENTAS (score combinado) ===")
print(f"{'Pos':4}{'CPID':16}{'Reviews':10}{'Visits':9}{'Items':7}{'Ventas(HTML)':14}{'Precio':10}Nombre")
for i,r in enumerate(RESULTS,1):
  print(f" {i:>3} {r['cpid']:14} {r['reviews']:>8}  {r['visits']:>7}  {r['items']:>5}   {str(r['ventas_HTML'] or '-'):>10}   ${r['price'] or '?':>6}  {r['name']}")

json.dump(RESULTS,open('/sessions/sharp-beautiful-lovelace/mnt/outputs/rosa_rank.json','w'),indent=2,default=str)
