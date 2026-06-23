import os,requests,json,re
API="https://api.mercadolibre.com"
CID=os.environ["MELI_APP_ID"]; CSEC=os.environ["MELI_APP_SECRET"]
RT=os.environ["MELI_REFRESH_TOKEN_ASVA"]
r=requests.post(f"{API}/oauth/token",data={"grant_type":"refresh_token","client_id":CID,"client_secret":CSEC,"refresh_token":RT},timeout=20)
AT=r.json()["access_token"]
H={"Authorization":f"Bearer {AT}"}
UA={"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"}

CPIDS={
 "Negro":["MLM44731940","MLM44731934","MLM68969359","MLM50967958","MLM63880644","MLM65836568","MLM50218388","MLM44710240","MLM37926169","MLM44710246","MLM44713972","MLM70496509","MLM44715070","MLM35996049"],
 "Celeste":["MLM61262890"],
 "Rosa":["MLM45700101","MLM65831856"],
 "Camuflaje":["MLM37361021","MLM70607552","MLM44722913"],
 "Negro+Celeste":["MLM54696427"],
}

RESULTS=[]
for tcol,cpids in CPIDS.items():
  for cpid in cpids:
    p=requests.get(f"{API}/products/{cpid}",headers=H,timeout=10).json()
    if p.get("status")!="active":
      continue
    name=p.get("name","")
    bbw=p.get("buy_box_winner") or {}
    price=bbw.get("price")
    
    # Scrape MELI catalog page to get "X vendidos"
    url=f"https://www.mercadolibre.com.mx/p/{cpid}"
    try:
      hh=requests.get(url,headers=UA,timeout=15)
      txt=hh.text
    except: txt=""
    sold_text=None
    # Look for patterns like "1.5k vendidos", "+500 vendidos", "10 vendidos"
    for pat in [r"(\d+(?:\.\d+)?[kK]?\s*[+­]?\s*vendid\w+)",
                r'"sold_quantity"\s*[:=]\s*(\d+)',
                r"vendidos?\":\s*(\d+)",
                r"(\d+(?:[.,]\d+)?)[\s ]?vendid"]:
      m=re.search(pat,txt,re.I)
      if m:
        sold_text=m.group(1)
        break
    
    # Get items count
    it=requests.get(f"{API}/products/{cpid}/items?limit=50",headers=H,timeout=10).json()
    items_total=it.get("paging",{}).get("total",0)
    items=it.get("results",[])
    
    # Get visits aggregate for top 10 items
    top_ids=[i.get("item_id") for i in items[:10] if i.get("item_id")]
    visits=0
    if top_ids:
      v=requests.get(f"{API}/visits/items?ids={','.join(top_ids)}",headers=H,timeout=10)
      if v.status_code==200:
        visits=sum((v.json() or {}).values())
    
    # Aggregate reviews across child items
    review_total=0
    for iid in top_ids[:5]:
      try:
        rv=requests.get(f"{API}/reviews/item/{iid}",headers=H,timeout=8).json()
        review_total+=rv.get("paging",{}).get("total",0)
      except: pass
    
    RESULTS.append({
      "cpid":cpid,"target_color":tcol,
      "name":name[:75],
      "ventas_HTML":sold_text,
      "items_count":items_total,
      "visits_top10":visits,
      "reviews_top5":review_total,
      "price":price,
      "url":url,
    })

# Sort by visits desc within each color group
RESULTS.sort(key=lambda x:(x["target_color"], -(x["visits_top10"] or 0)))
print(f"\n=== JBL GO 4 RANKING ({len(RESULTS)}) ===")
print(f"{'Color':12} {'CPID':14} {'Ventas(HTML)':15} {'Items':6} {'Visits':8} {'Reviews':8} {'Precio':8} {'Nombre'}")
for r in RESULTS:
  print(f"  {r['target_color']:10} {r['cpid']:14} {str(r['ventas_HTML']):15} {r['items_count']:>5} {r['visits_top10']:>7} {r['reviews_top5']:>7} ${r['price'] or '?':>6} | {r['name']}")

json.dump(RESULTS,open('/tmp/ranking.json','w'),indent=2,default=str)
