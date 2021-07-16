import os
import requests
from dotenv import load_dotenv
from pprint import pprint

load_dotenv()

class API:
    def __init__(self):
        self.headers = {"Authorization": os.getenv("OTP_API_KEY"), "Host": "gtfsr.vbn.de"}

    def get(self, url, post_args=None, data=None):
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

    def getStops(self, post_args):
        return self.get("http://gtfsr.vbn.de/api/routers/connect/index/stops", post_args)

    def getRoutes(self):
        return self.get("http://gtfsr.vbn.de/api/routers/connect/index/stops")

    def getPlan(self, data):
        return self.get("http://gtfsr.vbn.de/api/routers/connect/plan", data)

    def bestRoutes(self, data, goal, numberOfStations=20):
        nearestStations = []
        data['radius'] = 50
        count = 0
        while len(nearestStations) < numberOfStations and count < 30:
            nearestStations = self.getStops(data)
            count += 1
            # pprint((nearestStations))
            data['radius'] += 50
        # print(count)
        pprint("nearestStations: " + str(nearestStations))
        routes = {}
        # pos -> stations
        # stations -> goal
        for station in nearestStations:
            # pos -> stations
            pos = (data['lat'], data['lon'])
            # numItineraries just 1 path per route
            station_data = {'numItineraries': 1, 'toPlace': goal, 'fromPlace': pos,
                            'intermediatePlaces': (station['lat'], station['lon']), 'pathComparator': 'duration'}
            route = self.getPlan(station_data)
            # print(len(route))
            routes[station['name']] = route
            # breakpoint()
        return routes


if __name__ == "__main__":
    from consts import SEEDHOUSE
    from show_map import show_map
    api = API()
    post_args = {"lat": 52.267281,
                 "lon": 8.053190,
                 "radius": 500,
                 }
    best = api.bestRoutes(post_args, SEEDHOUSE)
    # stop_positions = {k: (v["plan"]["from"]["lat"], v["plan"]["from"]["lon"]) for k,v in best.items()}
    stop_positions = {k: [float(i) for i in v["requestParameters"]["intermediatePlaces"].split(",")] for k,v in best.items()}
    show_map(list(stop_positions.values())[0], list(stop_positions.values())[1], [(*i,"green") for i in stop_positions.values()])