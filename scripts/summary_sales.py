import os,requests,json,time
from datetime import datetime,timedelta

ACCOUNTS={
    "JUAN":os.environ.get("MELI_REFRESH_TOKEN"),
    "CLARIBEL":os.environ.get("MELI_REFRESH_TOKEN_CLARIBEL"),
    "ASVA":os.environ.get("MELI_REFRESH_TOKEN_ASVA"),
    "RAYMUNDO":os.environ.get("MELI_REFRESH_TOKEN_RAYMUNDO"),
}

now=datetime.utcnow()
today=now.strftime("%Y-%m-%dT00:00:00.000-00:00")
week_ago=(now-timedelta(days=7)).strftime("%Y-%m-%dT00:00:00.000-00:00")
month_ago=(now-timedelta(days=30)).strftime("%Y-%m-%dT00:00:00.000-00:00")
year_ago=(now-timedelta(days=365)).strftime("%Y-%m-%dT00:00:00.000-00:00")

REPORT={}
for label,rt in ACCOUNTS.items():
    if not rt: 
        REPORT[label]={"error":"sin token"}; continue
    r=requests.post("https://api.mercadolibre.com/oauth/token",data={"grant_type":"refresh_token","client_id":os.environ["MELI_APP_ID"],"client_secret":os.environ["MELI_APP_SECRET"],"refresh_token":rt}).json()
    if "access_token" not in r:
        REPORT[label]={"error":"refresh fail"}; continue
    H={"Authorization":f"Bearer {r['access_token']}"}
    me=requests.get("https://api.mercadolibre.com/users/me",headers=H).json()
    USER_ID=me["id"]
    nick=me.get("nickname")
    rep=me.get("seller_reputation") or {}
    
    # Total ordenes pagadas histórico
    o_total=requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.status=paid&limit=1",headers=H,timeout=15).json()
    total_paid=o_total.get("paging",{}).get("total",0)
    
    # Total cancelled
    o_canc=requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.status=cancelled&limit=1",headers=H,timeout=15).json()
    total_cancelled=o_canc.get("paging",{}).get("total",0)
    
    # Today
    o_today=requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.status=paid&order.date_created.from={today}&limit=50",headers=H,timeout=15).json()
    today_count=o_today.get("paging",{}).get("total",0)
    today_revenue=sum(o.get("total_amount",0) for o in (o_today.get("results") or []))
    
    # Week
    o_week=requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.status=paid&order.date_created.from={week_ago}&limit=50",headers=H,timeout=15).json()
    week_count=o_week.get("paging",{}).get("total",0)
    week_revenue=sum(o.get("total_amount",0) for o in (o_week.get("results") or []))
    
    # Month
    o_month=requests.get(f"https://api.mercadolibre.com/orders/search?seller={USER_ID}&order.status=paid&order.date_created.from={month_ago}&limit=50&sort=date_desc",headers=H,timeout=15).json()
    month_count=o_month.get("paging",{}).get("total",0)
    month_revenue=sum(o.get("total_amount",0) for o in (o_month.get("results") or []))
    
    # Items
    iA=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=active&limit=1",headers=H,timeout=15).json()
    iP=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=paused&limit=1",headers=H,timeout=15).json()
    iC=requests.get(f"https://api.mercadolibre.com/users/{USER_ID}/items/search?status=closed&limit=1",headers=H,timeout=15).json()
    
    REPORT[label]={
        "nickname":nick,"user_id":USER_ID,
        "reputation":rep.get("level_id","s/d"),"power_seller":rep.get("power_seller_status"),
        "total_paid":total_paid,
        "total_cancelled":total_cancelled,
        "today":{"orders":today_count,"revenue":round(today_revenue,2)},
        "week":{"orders":week_count,"revenue":round(week_revenue,2)},
        "month":{"orders":month_count,"revenue":round(month_revenue,2)},
        "items":{"active":iA.get("paging",{}).get("total",0),
                 "paused":iP.get("paging",{}).get("total",0),
                 "closed":iC.get("paging",{}).get("total",0)},
    }

print(json.dumps(REPORT,ensure_ascii=False,indent=2))
