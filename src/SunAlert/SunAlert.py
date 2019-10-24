
from flask import Flask
from flask import request
from flask import render_template
from flask import redirect
from flask import url_for
from flask import session
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

from sunpy.instr.goes import flux_to_flareclass
import astropy.units as u

from flask import Flask, render_template, request, make_response
from authomatic.adapters import WerkzeugAdapter
from authomatic import Authomatic

from config import CONFIG



database = Database('sqlite:///sunpydata.sqlite')

class Server():
    def __init__(self):
        print("Start server")

        self.printers = []
        self.printer_class = {}

        self.db = pymongo.MongoClient('localhost', 27017)['SunAlert']
        self.authomatic = Authomatic(CONFIG, 'your secret string', report_errors=False)

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
        self.app.add_url_rule('/live/state.json', 'state_json', self.current_state)
        self.app.add_url_rule('/printers', 'printers', self.get_printers)
        self.app.add_url_rule('/printer/<id>/', 'printer', self.printer)
        self.app.add_url_rule('/login/<provider_name>/', 'login', self.login)

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
        #data = pd.read_json("https://services.swpc.noaa.gov/json/goes/primary/xrays-1-day.json")
        return data.to_csv()

    def current_state(self):
        data = pd.read_json("https://services.swpc.noaa.gov/json/goes/15/goes15_xray_1m.json")
        
        last = data.iloc[0]['x_long']
        text_last = flux_to_flareclass(last* u.watt/u.m**2)

        max_24 = data['x_long'].max()
        text_max_24 = flux_to_flareclass(max_24*u.watt/u.m**2)

        out = {
            'last': last,
            'last_text': text_last,
            'max_24': max_24,
            'max_24_text': text_max_24,
        }
        print(" ")
        print(out)

        return jsonify(out)


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

    def login(self, provider_name):

        # We need response object for the WerkzeugAdapter.
        response = make_response()
        
        # Log the user in, pass it the adapter and the provider name.
        result = self.authomatic.login(WerkzeugAdapter(request, response), provider_name)
        
        # If there is no LoginResult object, the login procedure is still pending.
        if result:
            if result.user:
                # We need to update the user to get more info.
                result.user.update()
            
            # The rest happens inside the template.
            return render_template('login.html', result=result)
        
        # Don't forget to return the response.
        return response

if __name__ == '__main__':
    s = Server()
