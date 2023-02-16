from flask import Flask, request
import json
import logging
from redis_client import client

app = Flask(__name__)

@app.route('/api/v0.1/m2-customer-code')
def customer_codes():
    barcodes = request.args.get('barcodes')
    if(barcodes):
        status = 200
        message = json.loads(barcodes)
    else: 
        status = 400
        message = 'invalid or missing barcode query param'
    return { 'status' : status, 'message': message }
