import json
from replit import db, database

def recurse_prim(x):
  x = database.to_primitive(x)
  if isinstance(x, dict):
    return {k:recurse_prim(v) for k,v in x.items()}
  if isinstance(x,list):
    return [recurse_prim(y) for y in x]
  return x


#Loads in database from JSON
def loadDatabase(filename):
  for k in db.keys():
    del db[k]
  with open(f'./{filename}') as f:
    data = json.load(f)
  for k, v in data.items():
    db[k] = v

#Saves database to JSON
def saveDatabase(filename):
  data = {k:recurse_prim(v) for k,v in db.items()}
  with open(filename, "w") as outfile: 
      json.dump(data, outfile, sort_keys=True, indent=4)

print('Start')
loadDatabase('sampledatabase.json')
print('Done')