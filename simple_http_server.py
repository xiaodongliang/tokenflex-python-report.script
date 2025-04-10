#####################################################################
## Copyright (c) Autodesk, Inc. All rights reserved
## Written by APS Partner Development
##
## Permission to use, copy, modify, and distribute this software in
## object code form for any purpose and without fee is hereby granted,
## provided that the above copyright notice appears in all copies and
## that both that copyright notice and the limited warranty and
## restricted rights notice below appear in all supporting
## documentation.
##
## AUTODESK PROVIDES THIS PROGRAM "AS IS" AND WITH ALL FAULTS.
## AUTODESK SPECIFICALLY DISCLAIMS ANY IMPLIED WARRANTY OF
## MERCHANTABILITY OR FITNESS FOR A PARTICULAR USE.  AUTODESK, INC.
## DOES NOT WARRANT THAT THE OPERATION OF THE PROGRAM WILL BE
## UNINTERRUPTED OR ERROR FREE.
#####################################################################
import argparse
import json
import os
import requests
import http.server as SimpleHTTPServer
import socketserver
import sys
import urllib.parse as urlparse
import config.state as state
import config.env as env
import consumption_reporting as ConsumptionReporting
import urllib.parse
import base64
from http.server import HTTPServer

httpd = None


class APSCallbackHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        global httpd
        bits = urlparse.urlparse(self.path)
       

        if bits.path == urlparse.urlparse(state.args.APS_CALLBACK_URL).path:
            state.code = urlparse.parse_qs(bits.query)['code']
          
            data = {
                'client_id':os.getenv('APS_CLIENT_ID', state.args.APS_CLIENT_ID),
                'client_secret':os.getenv('APS_CLIENT_SECRET', state.args.APS_CLIENT_SECRET),
                'grant_type': 'authorization_code',
                'code': state.code,
                'redirect_uri': os.getenv('APS_CALLBACK_URL', state.args.APS_CALLBACK_URL)
            }
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            print(data)
            print(headers)
            resp = requests.post(env.access_token_url, headers=headers, data=data)
            if resp.status_code == 200:
                state.token = resp.json()['access_token']
                print(state.token)
                self.send_response(200)
                try:
                    ConsumptionReporting.start(state.token)
                    self.send_response(200)
                except Exception as e:
                    print(e)
                    self.send_response(500)
            else:
                print(resp.json())
                self.send_response(500)
            httpd.shutdown()
        else:
            self.send_response(404)


class ThreadingHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    allow_reuse_address = True


def startHttpServer():
    global httpd
    PORT = 3000
    httpd = ThreadingHTTPServer(("", PORT), APSCallbackHTTPRequestHandler)
    print("serving at port", PORT)
    httpd.serve_forever()

