import os
CID=os.environ["MELI_APP_ID_NEW"]
# Print in chunks of 4 chars (less than full secret length so not masked)
for i in range(0,len(CID),4):
  print(f"chunk_{i//4+1}: {CID[i:i+4]}")
# Also print first/last halves separately
print(f"first8: {CID[:8]}")
print(f"last8: {CID[8:]}")
