import requests
import logging
import sys
import time
import json

from urllib.parse import urlencode
from urllib.request import Request, urlopen

logging.basicConfig(filename='bricks.log', filemode='w+', level=logging.INFO)
logging.getLogger().addHandler(logging.StreamHandler())

MAIN_INTERVAL_MS = 10000
APIKEY = "tbd"
TYPE = "RaspberryPi"
CHIPID = "tbd"

def request():

    logging.info("starting request");
    # url = 'https://brewbricks.com/api/iot/v1'
    url = 'http://localhost:5001/bierbot-cloud/us-central1/iot_v1'

    post_fields = {
        "a_bool_epower_0": str(currentStateRelaisHeat), # TODO
        "s_number_temp_0": str(currentTempCelsius),     # TODO
        "type": "raspberryPi",
        "brand": "oss",
        "version": "0.9",
        "chipid": CHIPID,
        "apikey": APIKEY
    }  # Set POST fields here

    response = requests.get(url, params=post_fields)
    jsonResponse = json.loads(response.text)

    nextRequestMs = jsonResponse["next_request_ms"]

    if ("epower_0_state" in jsonResponse):
        currentStateRelaisHeat = jsonResponse["epower_0_state"]

    logging.info(f"sleeping for {nextRequestMs}ms")
    time.sleep(nextRequestMs / 1000)

import time

def current_milli_time():
    return round(time.time() * 1000)
  
def run():

    while True:
        msStart = current_milli_time()
        request()
        msPassed = current_milli_time() - msStart

if __name__ == '__main__':
    logging.info("BierBot Bricks RaspberryPi client started.")
    run()
