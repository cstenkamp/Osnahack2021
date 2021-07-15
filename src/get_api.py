import os
import requests
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

URL = "http://gtfsr.vbn.de/api/routers/connect/plan"

data = {"arriveBy": False,
        "date": "07-25-2021",
        "fromPlace": (53.08287,8.81334),
        "toPlace": (53.05270,8.78617),
        "time": "13:00:00",
        "mode": ("WALK","TRANSIT"),
        "maxWalkDistance": 300}

headers = {"Authorization": os.getenv("OTP_API_KEY"), "Host": "gtfsr.vbn.de"}
data = {k:
                str(v).lower() if isinstance(v, bool) else
                        v if not isinstance(v, (list,tuple)) else
                                ",".join([str(i) if not isinstance(i,float) else f"{i:.5f}" for i in v])
                for k,v in data.items()
        }

fullurl = URL[:-1] if URL.endswith("/") else URL
fullurl += "?"+"&".join(f"{k}={v}" for k,v in data.items())

tmp = requests.get(fullurl, headers=headers)
pprint(tmp.json())