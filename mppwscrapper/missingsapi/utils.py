import dataclasses
import datetime
import json
import logging
import urllib.error
import urllib.parse
import urllib.request

import ws.mpp

# BASE_URL = "http://extraviados.mx/api/v1/mpps"
BASE_URL = "http://localhost:8000/api/v1/mpps"


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        return json.JSONEncoder.default(self, obj)


def count_mpps_by_post_url(post_url: str) -> list[dict]:
    parsed_post_url = urllib.parse.quote_plus(post_url)
    url = f"{BASE_URL}/?po_post_url={parsed_post_url}"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                body = response.read().decode("UTF-8")
            else:
                return False
    except urllib.error.HTTPError as e:
        logging.exception("Unable to retrieve %s", url)
        return False
    except urllib.error.URLError as e:
        logging.exception("Unable to retrieve %s", url)
        return False

    try:
        api_res = json.loads(body)
    except json.JSONDecodeError as e:
        logging.exception("Unable parse the response from %s", url)
        return False

    return api_res["count"]


def create_mpp(mpp: ws.mpp.MissingPersonPoster, token: str):
    mpp_dict = dataclasses.asdict(mpp)
    req_body = json.dumps(mpp_dict, cls=CustomJSONEncoder).encode("UTF-8")
    url = f"{BASE_URL}/"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Token {token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, req_body) as response:
            if response.status != 201:
                return None
            res_body = response.read().decode("UTF-8")
    except urllib.error.HTTPError as e:
        logging.exception("Unable to POST to %s, %s", url, str(e))
        return None
    except urllib.error.URLError as e:
        logging.exception("Unable to POST to %s", url)
        return None

    try:
        api_res = json.loads(res_body)
    except json.JSONDecodeError as e:
        logging.exception("Unable parse the response from %s", url)
        return None

    return api_res
