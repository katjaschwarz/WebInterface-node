# -*- coding: utf-8 -*-
"""
Created on Thu Feb 27 09:25:24 2018
@author: jlibor
"""
### Aktuelle Version als Hilfe ausgeben
import os
import sys
import time
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer       # python 2
#from http.server import BaseHTTPRequestHandler, HTTPServer        # python 3
import json
# from SVM_embedding_global import compute_graph, learn_svm, multiclass_embed, local_embedding
from compute_embedding import compute_graph, learn_svm, local_embedding, train_global_svm, \
    local_embedding_with_all_positives, write_final_svm_output
"""
def format_string(graph):
    s = str(graph)
    s = s.replace("'", '"').replace(': ', ':').replace('False', 'false').replace('True', 'true')\
        .replace(', ', ',').replace(':u"', ':"')
    return s
"""

"""
### dev Server
def get_graph(userData = []):
    filename = "data/response_data.txt"
    with open(filename, "rb") as f:
        return f.read()
"""

## MyHTTPHandler beschreibt den Umgang mit HTTP Requests
class MyHTTPHandler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200, "ok")
        self.send_header('Access-Control-Allow-Origin', self.headers['origin'])
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-type')

        self.end_headers()


    def do_POST(self):
        """
        definiert den Umgang mit POST Requests
        Liest den Body aus - gibt in zum konvertieren weiter

        """
        if(self.path == "/nodes"):
            print("post /nodes")
            ### POST Request Header ###
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            #self.send_header('Access-Control-Allow-Origin', self.headers['origin'])
            self.end_headers()

            # get body from request
            content_len = int(self.headers['Content-Length'])
            body = self.rfile.read(content_len)

            # convert body to list
            data = json.loads(str(body).decode('utf-8'))  # python 2
            #data = json.loads(str(body, encoding='utf-8'))      # python 3
            # print(data)

            # Katjas code goes here
            nodes, categorys = compute_graph(data)
            # data = multiclass_embed(data)

            # make json
            data = json.dumps({'nodes': nodes, 'categorys': categorys}).encode()
            self.wfile.write(data)  #body zurueckschicken

        if(self.path == "/trainSvm"):
            print("post /trainsvm")
            ### POST Request Header ###
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # get body from request
            content_len = int(self.headers['Content-Length'])
            body = self.rfile.read(content_len)

            # convert body to list
            data = json.loads(str(body).decode('utf-8'))  # python 2
            #data = json.loads(str(body, encoding='utf-8'))      # python 3
            # print(data)

            # Katjas code goes here
            p, n, t = learn_svm(data['p'], data['n'], data['count'])

            # make json
            data = json.dumps({'p': p, 'n': n, 't': t}).encode()
            self.wfile.write(data)  #body zurueckschicken

        if(self.path == "/stopSvm"):
            print("post /stopSvm")
            ### POST Request Header ###
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()

            # get body from request
            #content_len = int(self.headers['Content-Length'])
            #body = self.rfile.read(content_len)

            # convert body to list
            #data = json.loads(str(body).decode('utf-8'))  # python 2
            #data = json.loads(str(body, encoding='utf-8'))      # python 3
            #print(data)

            # Katjas code goes here
            # triplet_constraints_from_svm()
            # train_global_svm()
            # local_embedding_with_all_positives(buffer=0.2, confidence_threshold=0.2)
            group_ids = write_final_svm_output()
            local_embedding(buffer=0.2)

            # make json
            data = json.dumps({'group': group_ids}).encode()
            self.wfile.write(data)  #body zurueckschicken


if __name__ == "__main__":
    # config
    HOST_NAME = ""
    PORT_NUMBER = 8000
    try:
        http_server = HTTPServer((HOST_NAME, PORT_NUMBER), MyHTTPHandler)
        print(time.asctime(), 'Server Starts - %s:%s' % (HOST_NAME, PORT_NUMBER), '- Beenden mit STRG+C')
        http_server.serve_forever()
    except KeyboardInterrupt:
        print(time.asctime(), 'Server Stops - %s:%s' % (HOST_NAME, PORT_NUMBER), '- Beenden mit STRG+C')
http_server.socket.close()