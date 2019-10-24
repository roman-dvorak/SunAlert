import pandas as pd
import pymongo
import json

data = pd.read_json("https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json")
print(data)
db = pymongo.MongoClient('localhost', 27017).SunAlert

for i, x in data.iterrows():
   #print(x['time_tag'])
    db.xray.update({'time_tag': x['time_tag']}, x.to_dict(), upsert = True)