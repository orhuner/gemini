import base64
import datetime
import hashlib
import hmac
import json
import time
import requests

base_url = "https://api.sandbox.gemini.com"
endpoint = "/v1/order/new"
url = base_url + endpoint

gemini_api_key = "account-oSVJF6Fvt20Px9SLyEWV"
gemini_api_secret = "2TQEk59mkFP8mp4F25n4g68rUgDY".encode()

t = datetime.datetime.now()
payload_nonce = str(int(time.mktime(t.timetuple()) * 1000))
int_nonce = int(time.mktime(t.timetuple()) * 1000)

payload = {
    "request": "/v1/order/new",
    "nonce": payload_nonce,
    "symbol": "btcusd",
    "amount": "5",
    "price": "3633.00",
    "side": "buy",
    "type": "exchange limit",
    "options": ["maker-or-cancel"]
}

encoded_payload = json.dumps(payload).encode()
b64 = base64.b64encode(encoded_payload)
signature = hmac.new(gemini_api_secret, b64, hashlib.sha384).hexdigest()

request_headers = {'Content-Type': "text/plain",
                   'Content-Length': "0",
                   'X-GEMINI-APIKEY': gemini_api_key,
                   'X-GEMINI-PAYLOAD': b64,
                   'X-GEMINI-SIGNATURE': signature,
                   'Cache-Control': "no-cache"}

# response = requests.post(url,
#                          data=None,
#                          headers=request_headers)

def create_payload(symbol, amount, price, side, order_type, options, nonce):
    return {
        'request': '/v1/order/new',
        'nonce': nonce,
        'symbol': symbol,
        'amount': amount,
        'price': price,
        'side': side,
        'type': order_type,
        'options': options
    }

def place_new_order(order_url, symbol, amount, price, side, order_type, options, nonce):
    payload = create_payload(symbol, amount, price, side, order_type, options, nonce)
    response = requests.post(order_url,
                             data=payload,
                             headers=request_headers)
    # print(response.json())
    return response



def test_create_successful_buy_order():
    response = place_new_order(url, 'btcusd', '5', '3633.00', 'buy', 'exchange limit', ['maker-or-cancel'], payload_nonce)
    response_body = response.json()
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/json"
    assert response_body['exchange'] == 'gemini'
    assert response_body['side'] == 'buy'
    assert response_body['is_live'] == True
    print(response_body)


# test_create_successful_buy_order()

# place_new_order(url, 'btcusd', '5', '3633.00', 'buy', 'exchange limit', ['maker-or-cancel'], payload_nonce)
# new_order = response.json()
# print(new_order)
