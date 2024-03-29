import pandas as pd
import pymongo
import json

data = pd.read_json("https://services.swpc.noaa.gov/json/goes/primary/xray-flares-7-day.json")
print(data)
db = pymongo.MongoClient('localhost', 27017).SunAlert

for i, x in data.iterrows():
    print(x['begin_time'])
    db.flares.update({'begin_time': x['begin_time']}, x.to_dict(), upsert = True)