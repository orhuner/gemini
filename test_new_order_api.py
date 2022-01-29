import base64
import datetime
import hashlib
import hmac
import json
import time
import requests
import time
import pytest


class TestNewOrderEndpoint:
    base_url = "https://api.sandbox.gemini.com"
    endpoint = "/v1/order/new"
    url = base_url + endpoint

    def teardown_method(self):
        time.sleep(.5)

    gemini_api_key = "account-oSVJF6Fvt20Px9SLyEWV"
    gemini_api_secret = "2TQEk59mkFP8mp4F25n4g68rUgDY".encode()

    def set_nonce(self):
        t = datetime.datetime.now()
        nonce = str(int(time.mktime(t.timetuple()) * 1000))
        return nonce

    def encode_payload(self, payload):
        encoded_payload = json.dumps(payload).encode()
        b64 = base64.b64encode(encoded_payload)
        return b64

    def set_request_headers(self, gemini_api_key, payload):
        encoded_payload = self.encode_payload(payload)
        signature = hmac.new(self.gemini_api_secret, encoded_payload, hashlib.sha384).hexdigest()
        request_headers = {'Content-Type': "text/plain",
                       'Content-Length': "0",
                       'X-GEMINI-APIKEY': gemini_api_key,
                       'X-GEMINI-PAYLOAD': encoded_payload,
                       'X-GEMINI-SIGNATURE': signature,
                       'Cache-Control': "no-cache"}
        return request_headers

    def create_payload(self, url, symbol, amount, price, side, order_type, options, stop_order=None):
        nonce = self.set_nonce()
        time.sleep(.5)
        payload = {
            'request': '/v1/order/new',
            'nonce': nonce,
            'symbol': symbol,
            'amount': amount,
            'price': price,
            'side': side,
            'type': order_type,
            'options': options
        }
        if stop_order:
            payload['stop_price'] = stop_order
        return payload

    def place_new_order(self, url, payload, request_headers):
        response = requests.post(url,
                                 data=payload,
                                 headers=request_headers)

        return response

    def test_create_successful_buy_order(self):
        # validate order is buy side limit order and check status of order
        payload = self.create_payload(self.url, "btcusd", "5", "3633.00", "buy", "exchange limit", ["maker-or-cancel"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        response_body = response.json()
        assert response.status_code == 200
        assert response.headers["Content-Type"] == "application/json"
        assert response_body["exchange"] == "gemini"
        assert response_body["side"] == "buy"
        assert response_body["is_live"] == True

    def test_create_successful_sell_order(self):
        payload = self.create_payload(self.url, "btcusd", "5", "3633.00", "sell", "exchange limit", ["maker-or-cancel"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response.headers["Content-Type"] == "application/json"
        assert response_body["side"] == "sell"
        assert response_body["symbol"] == "btcusd"

    def test_exchange_limit_request(self):
        payload = self.create_payload(self.url, "btcusd", "5", "40000.00", "sell", "exchange limit", ["maker-or-cancel"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["symbol"] == "btcusd"
        assert response_body["type"] == "exchange limit"

    def test_currency_parameter(self):
        payload = self.create_payload(self.url, "ethusd", "5", "500.00", "sell", "exchange limit", ["maker-or-cancel"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["symbol"] == "ethusd"

    def test_stop_limit_buy_request(self):
        payload = self.create_payload(self.url, "btcusd", "5", "40000.00", "buy", "exchange limit", ["maker-or-cancel"], "42000.00")
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["side"] == "buy"
        assert response_body["symbol"] == "btcusd"
        assert response_body["type"] == "exchange limit"

    def test_stop_limit_sell_request(self):
        payload = self.create_payload(self.url, "btcusd", "5", "40000.00", "sell", "exchange limit", ["maker-or-cancel"], "42000.00")
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["side"] == "sell"
        assert response_body["symbol"] == "btcusd"
        assert response_body["type"] == "exchange limit"

    def test_empty_options_standard_limit_order_request(self):
        payload = self.create_payload(self.url, "btcusd", "5", "40000.00", "sell", "exchange limit", [], "42000.00")
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["side"] == "sell"
        assert response_body["type"] == "exchange limit"

    def test_empty_options_standard_limit_order_request(self):
        payload = self.create_payload(self.url, "btcusd", "5", "40000.00", "sell", "exchange limit", [], "42000.00")
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["side"] == "sell"
        assert response_body["options"] == []
        assert response_body["is_cancelled"] == False

    def test_original_and_remaining_amount(self):
        # Without any execution the remaining amount should be the same as original amount
        payload = self.create_payload(self.url, "btcusd", "10", "40000.00", "sell", "exchange limit", [], "42000.00")
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["side"] == "sell"
        assert response_body["options"] == []
        assert response_body["is_cancelled"] == False
        assert response_body["original_amount"] == "10"
        assert response_body["remaining_amount"] == "10"

    def test_immediate_or_cancel_order(self):
        # Assumption: Since there are no other orders on the orderbook, the order won't be filled and cancelled.
        # The execution scenario can be tested with multiple users
        payload = self.create_payload(self.url, "btcusd", "5", "40000.00", "sell", "exchange limit", ["immediate-or-cancel"], "42000.00")
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["side"] == "sell"
        assert response_body["options"] == ["immediate-or-cancel"]
        assert response_body["is_cancelled"] == True

    def test_fill_or_kill_order_type(self):
        # Assumption: Since there are no other orders on the orderbook, the order won't be filled and cancelled.
        # The execution scenario can be tested with multiple users
        payload = self.create_payload(self.url, "btcusd", "5", "40000.00", "sell", "exchange limit", ["fill-or-kill"], "42000.00")
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["side"] == "sell"
        assert response_body["options"] == ['fill-or-kill']
        assert response_body["is_cancelled"] == True

    @pytest.mark.skip(reason="receiving 400 with exchange limit orders")
    def test_auction_only_order_type(self):
        payload = self.create_payload(self.url, "btcusd", "5", "3655.00", "sell", "exchange limit", ["auction-only"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["side"] == "sell"
        assert response_body["options"] == ['auction-only']
        assert response_body["is_cancelled"] == True

    @pytest.mark.skip(reason="receiving 400 with exchange limit orders")
    def test_indication_of_interest(self):
        payload = self.create_payload(self.url, "btcusd", "5", "3655.00", "sell", "exchange limit", ["indication-of-interest"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["side"] == "sell"
        assert response_body["options"] == ['indication-of-interest']
        assert response_body["is_cancelled"] == True

    # Negative test cases
    def test_non_increasing_nonce(self):
        # test against a replay attack by attempting to use a non increasing nonce value for second order attempt
        nonce = self.set_nonce()
        payload = {
            'request': '/v1/order/new',
            'nonce': nonce,
            'symbol': 'btcusd',
            'amount': '5',
            'price': '40000.00',
            'side': 'buy',
            'type': 'exchange limit',
            'options': ["maker-or-cancel"]
        }

        encoded_payload = self.encode_payload(payload)
        signature = hmac.new(self.gemini_api_secret, encoded_payload, hashlib.sha384).hexdigest()
        request_headers = {'Content-Type': "text/plain",
                           'Content-Length': "0",
                           'X-GEMINI-APIKEY': self.gemini_api_key,
                           'X-GEMINI-PAYLOAD': encoded_payload,
                           'X-GEMINI-SIGNATURE': signature,
                           'Cache-Control': "no-cache"}
        response = self.place_new_order(self.url, payload, request_headers)
        # first order should be ok with a valid nonce
        assert response.status_code == 200
        response = self.place_new_order(self.url, payload, request_headers)
        response_body = response.json()
        # second order has invalid nonce so 400 error message is sent by server
        assert response.status_code == 400
        assert response_body['reason'] == "InvalidNonce"
        assert response_body['message'] == "Nonce '{}' has not increased since your last call to the Gemini API.".format(nonce)

    def test_low_limit_sell_order(self):
        payload = self.create_payload(self.url, "btcusd", "5", "2.00", "sell", "exchange limit",
                                      ["maker-or-cancel"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["is_cancelled"] == True

    def test_high_limit_buy_order(self):
        payload = self.create_payload(self.url, "btcusd", "5", "200000.00", "buy", "exchange limit",
                                      ["maker-or-cancel"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        assert response.status_code == 200
        response_body = response.json()
        assert response_body["is_cancelled"] == True
        assert response_body["is_live"] == False
        assert response_body["reason"] == 'MakerOrCancelWouldTake'

    def test_invalid_price(self):
        payload = self.create_payload(self.url, "btcusd", "5", "-40000.00", "sell", "exchange limit",
                                      ["maker-or-cancel"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        response_body = response.json()
        assert response.status_code == 400
        assert response_body["reason"] == "InvalidPrice"

    def test_invalid_side_btcusd(self):
        payload = self.create_payload(self.url, "btcusd", "5", "40000.00", "test", "exchange limit",
                                      ["maker-or-cancel"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        response_body = response.json()
        assert response.status_code == 400
        assert response_body["reason"] == "InvalidSide"
        assert response_body["message"] == "Invalid side for symbol BTCUSD: 'test'"

    def test_invalid_side_ethusd(self):
        payload = self.create_payload(self.url, "ethusd", "5", "40000.00", "test", "exchange limit",
                                      ["maker-or-cancel"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        response_body = response.json()
        assert response.status_code == 400
        assert response_body["reason"] == "InvalidSide"
        assert response_body["message"] == "Invalid side for symbol ETHUSD: 'test'"

    def test_multiple_options_are_not_permitted(self):
        payload = self.create_payload(self.url, "btcusd", "5", "200000.00", "buy", "exchange limit",
                                      ["maker-or-cancel", "fill-or-kill"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        response_body = response.json()
        assert response.status_code == 400
        assert response_body["reason"] == "ConflictingOptions"
        assert response_body["message"] == "A single order supports at most one of these options: ['maker-or-cancel', " \
                             "'immediate-or-cancel', 'auction-only', 'fill-or-kill']"

    def test_invalid_options(self):
        payload = self.create_payload(self.url, "btcusd", "5", "40000.00", "buy", "exchange limit",
                                      ["test"])
        request_headers = self.set_request_headers(self.gemini_api_key, payload)
        response = self.place_new_order(self.url, payload, request_headers)
        response_body = response.json()
        assert response.status_code == 400
        assert response_body["reason"] == "UnsupportedOption"
        assert response_body["message"] == 'Option "test" is not supported.'

    def test_invalid_signature(self):
        nonce = self.set_nonce()
        payload = {
            'request': '/v1/order/new',
            'nonce': nonce,
            'symbol': 'btcusd',
            'amount': '5',
            'price': '40000.00',
            'side': 'buy',
            'type': 'exchange limit',
            'options': ["maker-or-cancel"]
        }

        encoded_payload = self.encode_payload(payload)
        signature = hmac.new(self.gemini_api_secret, encoded_payload, hashlib.sha384).hexdigest()
        request_headers = {'Content-Type': "text/plain",
                           'Content-Length': "0",
                           'X-GEMINI-APIKEY': "account-ABCDF6Fvt20Px9SLyXYZ",
                           'X-GEMINI-PAYLOAD': encoded_payload,
                           'X-GEMINI-SIGNATURE': signature,
                           'Cache-Control': "no-cache"}
        response = self.place_new_order(self.url, payload, request_headers)
        response_body = response.json()
        assert response.status_code == 400
        response_body['reason'] = 'InvalidSignature'
        response_body['message'] = 'InvalidSignature'