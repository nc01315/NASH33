import re
import os
import sys
import array
import uuid
import csv
import random
import json
from contextlib import contextmanager
from locust.contrib.fasthttp import ResponseContextManager
import time
import logging
from locust import HttpUser, SequentialTaskSet, task, between, events, web, TaskSet
import requests
from datetime import datetime

USER_CREDENTIALS = None

path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, f'{path}')

import prommodule

class UserBehaviour(SequentialTaskSet):

    def __init__(self, parent):
        super().__init__(parent)
        self.customerPaymentId = ""
        self.allPayment = []
        self.guid = str(uuid.uuid4())
        self.redirectResult = str(uuid.uuid4())
        self.orderId = str(uuid.uuid4())
        self.orderId2 = str(uuid.uuid4())
        self.userid = "22826000000000052"
        if len(USER_CREDENTIALS) > 0:
            rand = ' '.join(random.choice(USER_CREDENTIALS))
            self.userid = rand

    def on_start(self):
        self.client.headers['Content-Type'] = "application/json"
        self.client.headers['mcd-dcsid'] = self.userid
        self.client.headers['Accept-Language'] = "en-GB"
        self.client.headers['mcd-marketid'] = "UK"
        self.client.headers['mcd-correlation-id'] = self.guid
        self.client.headers['mcd-deviceplatform'] = "Android"


    @task
    def add_card(self, addCardResponse=None):
        addCardPaypalPayload = {
            "accountName": "youremail@email.com",
            "redirectResult": self.redirectResult,
            "clientInfo": {
                "device": {
                    "pspTransactionId": "74d7157b1ec624fb92af0e04d21e7b121"
                }
            }
        }

        with self.client.post("/exp/v1/wallet/account/paypal/redirect", name="Paypal_AddCard",
                              json=addCardPaypalPayload, catch_response=True) as addCardPaypal:

            addCardPaypalJson = addCardPaypal.json()
            if addCardPaypal.status_code == 200 or addCardPaypal.status_code == 2000:
                addCardPaypal.success()
                for i in addCardPaypalJson['response']['paymentAccounts']:
                    customerpaymentid = str(i.get('customerPaymentMethodId'))
                self.customerPaymentId = customerpaymentid.replace("'", "")
            else:
                addCardPaypal.failure("Failed to addCard, the response code was: " + str(addCardPaypal.status_code))

    @task
    def checkoutv1(self):
        checkoutPayloadV1 = {
            "orderAmount": 500,
            "merchantAccount": "MCD_UK_12345",
            "orderId": self.orderId2,
            "store": 455,
            "CardId":self.customerPaymentId,
            "Instrument": 3
        }

        with self.client.post("https://paymentms-payments-uk-perf02.stage-perf2.us-east-1.stage.digitalecp.mcd.com/api/Payment/checkout", name="Paypal_CheckoutV1", json=checkoutPayloadV1,
                              catch_response=True) as checkoutv1Response:
            if checkoutv1Response.status_code == 200 and "" in checkoutv1Response.text:
                checkoutv1Response.success()
            else:
                checkoutv1Response.failure("Failed to execute checkout V2" + checkoutv1Response.text)


    @task
    def checkoutv2(self):
        checkoutPayload = {
            "OrderId": self.orderId,
            "OrderAmount": 500,
            "CardId": self.customerPaymentId,
            "merchantAccount": "MCD_UK_12345",
            "Store": 455,
            "ThreeDs2": {},
            "Instrument": 3,
            "ProductItems": [
                {
                    "Id": "721",
                    "Quantity": 1,
                    "Amount": 129,
                    "TaxAmount": 10,
                    "Description": "M Sprite"
                }
            ],
            "OrderType": 1,
            "Metadata": {
                "TerminalId": ""
            },
            "ReturnUrl": "mcdmobileapp://3ds1_return",
            "Order_Type": "Delivery"
        }

        with self.client.post("http://paymentms-payments-uk-perf02.stage-perf2.us-east-1.stage.digitalecp.mcd.com/api/Payment/V2/checkout/455", name="Paypal_CheckoutV2", json=checkoutPayload,
                              catch_response=True) as checkoutv2Response:
            if checkoutv2Response.status_code == 200 and "" in checkoutv2Response.text:
                checkoutv2Response.success()
            else:
                checkoutv2Response.failure("Failed to execute checkout V2" + checkoutv2Response.text)


    @task
    def get_wallet(self):
        with self.client.get("/exp/v1/wallet", name="Paypal_GetWallet", catch_response=True) as GetPaypalResponse:

            # get StoredPaymentId
            try:
                json_response = GetPaypalResponse.json()
                for i in json_response['response']['paymentAccounts']:
                    customerpaymentid = str(i['customerPaymentMethodId'])
                    cust = customerpaymentid.replace("'", "")
                    self.allPayment.append(cust)
            except:
                self.customerPaymentId = ""

            if GetPaypalResponse.status_code == 200 and "The call was successful." in GetPaypalResponse.text:
                GetPaypalResponse.success()
            else:
                GetPaypalResponse.failure("Failed to GetWallet, the message was: " + GetPaypalResponse.text)

    @task
    def delete_card(self):
        for ID in self.allPayment:
            with self.client.delete("/exp/v1/wallet/" + ID, name="Paypal_DeleteCard",
                                catch_response=True) as DeleteResponse:
                if DeleteResponse.status_code == 204:
                    DeleteResponse.success()
                else:
                    DeleteResponse.failure("Failed to deleteCard, the response was: " + DeleteResponse.text)
        self.allPayment = []


@events.init.add_listener
def locust_init(environment, **kwargs):
    global USER_CREDENTIALS

    if USER_CREDENTIALS == None:
        with open(f"{path}/data.csv") as f:
            reader = csv.reader(f)
            USER_CREDENTIALS = list(reader)
            USER_CREDENTIALS.pop()

class WalletRequests(HttpUser):
    tasks = [UserBehaviour]
    wait_time = between(1, 2)



stats = {}



@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    prommodule.on_stop(environment, **kwargs)
'''
def on_test_stop(environment, **kwargs):
    if environment.web_ui:
        time.sleep(3)
        s = environment.stats
        send_stats_to_pushgateway(s)
        if environment.stats.total.fail_ratio > 0.1:
            logging.error("Test failed due to failure ratio > 10%")
            environment.process_exit_code = 1
        else:
            environment.process_exit_code = 0
        
def _submit_wrapper(job_name, metric_name, metric_value):
    headers = {'X-Requested-With': 'Python requests', 'Content-type': 'text/xml'}
    requests.post('http://%s/metrics/job/%s' % (os.environ['PROM_PUSHGATEWAY'], job_name),
                  data='%s %s\n' % (metric_name, metric_value), headers=headers)


        
def send_stats_to_pushgateway(stats):
    s = stats.total
    arr = s.percentile()
    resp_per = arr.split()
    resp_per = resp_per[1:-1]
    num_requests = str(s.num_requests)
    num_failures = str(s.num_failures)
    target_per = resp_per[4]
    rps = s.total_rps

    jobname = os.environ['PROM_JOBNAME']

    entries = stats.entries
    list_entries = list(entries.keys())
    
    _submit_wrapper(jobname, 'locust_total_requests', num_requests)
    _submit_wrapper(jobname, 'locust_total_failures', num_failures)
    _submit_wrapper(jobname, 'locust_90th_percentile', target_per)
    _submit_wrapper(jobname, 'locust_requests_per_second', str(rps))

    for ent in list_entries:
        name = ent[0]
        method = ent[1]
        var_percentile = stats.get(name, method).get_response_time_percentile(0.90)
        var_requests = stats.get(name, method).num_requests
        var_failures = stats.get(name, method).num_failures
        var_rps = stats.get(name, method).total_rps

        _submit_wrapper(jobname, 'locust_' + name + '_requests', var_requests)
        _submit_wrapper(jobname, 'locust_' + name + '_failures', var_failures)
        _submit_wrapper(jobname, 'locust_' + name + '_90th_percentile', var_percentile)
        _submit_wrapper(jobname, 'locust_' + name + '_requests_per_second', str(var_rps))
'''
