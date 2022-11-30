import os
import logging
import time
import uuid
from datetime import datetime
from locust import HttpUser, SequentialTaskSet, task, between, events, web, TaskSet, constant_throughput
import csv
import random
import sys

path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, f'{path}')

import prommodule

USER_CREDENTIALS = None

class UserBehaviour(SequentialTaskSet):
  
	
	
    def __init__(self, parent):
        super().__init__(parent)
        #c = 1/0
        print(c)
        self.userid = ""
        self.customerPaymentId = ""
        self.guid = str(uuid.uuid4())
        self.userid = "22826000000000052"
        if len(USER_CREDENTIALS) > 0:
            rand = ' '.join(random.choice(USER_CREDENTIALS))
            self.userid = rand
        print(self.userid)

    def on_start(self):
        #c = 1/0
        print(c)
        self.client.headers['Content-Type'] = "application/json"
        self.client.headers['mcd-dcsid'] = self.userid
        self.client.headers['Accept-Language'] = "en-GB"
        self.client.headers['mcd-marketid'] = "UK"
        self.client.headers['mcd-correlation-id'] = self.guid
        self.client.headers['mcd-deviceplatform'] = "Android"
        print(self.client.headers['mcd-dcsid'])

    @task
    def pef_test(self):
        #c = 1/0
        print(c)
        with self.client.get("/", name="get", catch_response=True) as response:
            try:
                json_response = response.json()
            except:
                print("*********************** TRY FAILED*****************")
        if response.status_code == 200:
            response.success()
        else:
            response.failure("Failed to GetWallet, the message was: " + response.text)
    
    wait_time = constant_throughput(1.0)
    
class WalletRequests(HttpUser):
    tasks = [UserBehaviour]


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    prommodule.on_stop(environment, **kwargs)
    #c = 1/0
    print(c)


@events.init.add_listener
def locust_init(environment, **kwargs):

    global USER_CREDENTIALS
    #c = 1/0
    print(c)

    if USER_CREDENTIALS == None:
        with open(f"{path}/data.csv") as f:
            reader = csv.reader(f)
            USER_CREDENTIALS = list(reader)
            USER_CREDENTIALS.pop()