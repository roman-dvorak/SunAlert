
from flask import Flask
from flask import request
from flask import render_template
from flask import redirect
from flask import url_for
from flask import jsonify
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from flask import json
from redis import Redis
from rq import Queue
from rq_scheduler import Scheduler
import requests

import pymongo
import json
import bson
import bson.json_util

import time
import datetime
import os 
import sys
import pandas as pd
import requests
#from .api import Api

import matplotlib.pyplot as plt
import datetime
from sunpy.timeseries import TimeSeries
from sunpy.time import TimeRange, parse_time
from sunpy.net import hek, Fido, attrs as a
from bokeh.embed import file_html
from bokeh.resources import CDN
from sunpy.database import Database



import io
import base64

import mpld3
from mpld3 import plugins

from bokeh.plotting import figure, show, output_file    
from bokeh.layouts import gridplot
from bokeh.plotting import figure, show, output_file
from bokeh.models import Span
from bokeh.embed import components

class printer():
    def __init__(self, name, url, api_key):
        self.name = name
        self.url = url
        self.api_key = api_key

    def get_version(self):
        headers = {
            'Content-Type': 'application/json',
            'X-Api-Key': self.api_key
            }
        print("ZJISTI STAV!", self.url+"/api/version")
        response = requests.get(self.url+"/api/version", headers=headers)
        return(str(response.content))


database = Database('sqlite:///sunpydata.sqlite')

class Server():
    def __init__(self):
        print("Start server")

        self.printers = []
        self.printer_class = {}

        self.db = pymongo.MongoClient('localhost', 27017)['SunAlert']

        self.app = Flask('SunAlert')
        self.start()

        self.app.config['TEMPLATES_AUTO_RELOAD'] = True
        self.app.config['TESTING'] = True
        self.app.config['DEBUG'] = True
        self.app.config['ENV'] = "development"
        self.app.run(host="0.0.0.0", port=9999)



    def start(self):
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/live', 'live', self.live)
        self.app.add_url_rule('/live/data.csv', 'live_data', self.graph_sp)
        self.app.add_url_rule('/live/data.json', 'live_data_json', self.graph_json)
        self.app.add_url_rule('/printers', 'printers', self.get_printers)
        self.app.add_url_rule('/printer/<id>/', 'printer', self.printer)

    def live(self):
        return render_template('live.html', title = "Live")

    def graph_sp(self):

        now = datetime.datetime.now()
        length = datetime.timedelta(hours = 24*2)
        tr = TimeRange([now - length, now])
        results = Fido.search(a.Time(tr), a.Instrument('XRS'))
        
        print("Nalezene soubory", results)
        files = Fido.fetch(results)
        goes = TimeSeries(files, source='XRS', concatenate=True)

        #goes = database.add_from_vso_query_result(results)
        #print(goes)

        client = hek.HEKClient()
        flares_hek = client.search(hek.attrs.Time(tr.start, tr.end), hek.attrs.FL, hek.attrs.FRM.Name == 'SWPC')
        #out = goes.data.to_json(orient='index', date_format='iso')
        print(goes.data)
        out = goes.data.rolling(20, min_periods=1).mean().to_csv()
        print(flares_hek)
        
        return out

    def graph_json(self):
        data = pd.read_json("https://services.swpc.noaa.gov/json/goes/15/goes15_xray_1m.json")
        return data.to_csv()




    def index(self):
        print(request)
        print(request.json)
        print(request.data)
        #result = self.queue.enqueue(long)
        return render_template('index.html', title='Home')
        

    def get_printers(self, status = True):
        response = self.app.response_class(
            response=bson.json_util.dumps(self.pf.get_printers(update = True)),
            status=200,
            mimetype='application/json'
        )
        return response

    def printer(self, id):
        id = bson.ObjectId(id)
        p = self.pf.get_printer(id, update = True)
        print(p['name'])
        return(bson.json_util.dumps(p))

if __name__ == '__main__':
    s = Server()
