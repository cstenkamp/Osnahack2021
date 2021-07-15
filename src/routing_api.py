import os
import requests
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

class API:
    def __init__(self):
        self.headers = {"Authorization": os.getenv("OTP_API_KEY"), "Host": "gtfsr.vbn.de"}

    def get(self, url, post_args, data=None):
        post_args = {k:
                             str(v).lower() if isinstance(v, bool) else
                             v if not isinstance(v, (list, tuple)) else
                             ",".join([str(i) if not isinstance(i, float) else f"{i:.5f}" for i in v])
                     for k, v in post_args.items()
                     }

        fullurl = url[:-1] if url.endswith("/") else url
        fullurl += "?" + "&".join(f"{k}={v}" for k, v in post_args.items())
        kwargs = {"headers": self.headers}
        if data:
            kwargs["data"] = data
        response = requests.get(fullurl, **kwargs)
        if response.status_code != 200:
            print(f"Err {response.status_code}")
            raise Exception()
        else:
            return response.json()