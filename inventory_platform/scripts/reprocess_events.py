"""Re-procesa eventos en status='pending' o 'error' (con retry limit)."""
import os,requests,psycopg2
DSN=os.environ["SUPABASE_DB_URL"]
GHT=os.environ["GH_TOKEN"]
conn=psycopg2.connect(DSN); cur=conn.cursor()
cur.execute("""SELECT id, topic, resource, user_id FROM events
    WHERE processing_status IN ('pending','error') AND attempts<5
    ORDER BY ts LIMIT 50""")
rows=cur.fetchall()
print(f"reprocessing {len(rows)} events")
for eid,topic,resource,user_id in rows:
    r=requests.post(f"https://api.github.com/repos/kxmwnzbzhn-spec/meli-autoresponder/dispatches",
        headers={"Authorization":f"Bearer {GHT}","Accept":"application/vnd.github+json"},
        json={"event_type":"meli_event","client_payload":{"event_id":eid,"topic":topic,"resource":resource,"user_id":user_id}})
    print(f"  event {eid} dispatch={r.status_code}")
cur.close(); conn.close()
